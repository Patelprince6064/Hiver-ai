#!/usr/bin/env python3
"""Build the historical support knowledge base.

Usage:
    python scripts/build_knowledge_base.py
    python scripts/build_knowledge_base.py --seed 42
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.knowledge_schema import KnowledgeRecord, validate_knowledge_base
from src.retrieval.response_pairing import pair_customer_support_messages, build_conversation_context
from src.retrieval.resolution_extraction import extract_resolution_type, build_retrieval_text
from src.retrieval.quality_filter import apply_quality_flags, categorize_quality, detect_duplicates
from src.intents.semantic_classifier import SemanticIntentClassifier
from src.intents.tfidf_baseline import preprocess_text


def find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "configs" / "knowledge_base.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_dataset(config: dict) -> pd.DataFrame | None:
    """Load the dataset based on configuration."""
    project_config_path = PROJECT_ROOT / "configs" / "project.yaml"
    with open(project_config_path, "r") as f:
        project_config = yaml.safe_load(f)

    selected_brand = project_config.get("dataset", {}).get("selected_brand")
    if not selected_brand:
        print("Error: No brand selected.")
        print("Run: python scripts/compute_brand_statistics.py")
        return None

    selected_brand_dir = PROJECT_ROOT / project_config["dataset"]["selected_brand_dir"]

    # Try to load from splits first
    splits_dir = PROJECT_ROOT / "data" / "processed" / "splits"
    if config.get("source", {}).get("use_train_split", True):
        train_path = splits_dir / "train.csv"
        if train_path.exists():
            df = pd.read_csv(train_path, low_memory=False)
            print(f"Loaded TRAIN split: {len(df):,} messages")
            return df

    # Fallback to selected brand messages
    messages_path = selected_brand_dir / "messages.csv"
    if messages_path.exists():
        df = pd.read_csv(messages_path, low_memory=False)
        print(f"Loaded selected brand messages: {len(df):,} messages")
        return df

    print("Error: No dataset found.")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Build knowledge base.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    project_root = find_project_root()
    config = load_config()

    # Load dataset
    print("Loading dataset...")
    df = load_dataset(config)
    if df is None:
        return 1

    # Detect columns
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "conversation" in col_lower or "thread" in col_lower:
            col_map["conversation_id"] = col
        elif col_lower in ["text", "message", "content", "tweet"]:
            col_map["text"] = col
        elif "author" in col_lower or "user" in col_lower or "sender" in col_lower:
            col_map["author"] = col
        elif "id" in col_lower and "tweet" in col_lower:
            col_map["tweet_id"] = col
        elif "time" in col_lower or "date" in col_lower or "created" in col_lower:
            col_map["timestamp"] = col

    print(f"Column mapping: {col_map}")

    # Pair customer-support messages
    print("\nPairing customer-support messages...")
    pairs = pair_customer_support_messages(df, col_map)
    print(f"Found {len(pairs):,} customer-support pairs")

    if not pairs:
        print("No customer-support pairs found. Check dataset structure.")
        return 1

    # Try to load intent classifier
    print("\nLoading intent classifier...")
    intent_clf = None
    save_dir = project_root / "models" / "semantic_classifier"
    if save_dir.exists():
        try:
            intent_clf = SemanticIntentClassifier.load(save_dir)
            print("Loaded semantic classifier")
        except Exception as e:
            print(f"Could not load classifier: {e}")

    # Build knowledge records
    print("\nBuilding knowledge records...")
    records = []
    kb_counter = 0

    for pair in pairs:
        customer_msg = pair["customer_message"]
        support_resp = pair["support_response"]

        # Skip empty messages
        if not customer_msg.strip() or not support_resp.strip():
            continue

        # Extract resolution
        resolution_type, resolution_evidence = extract_resolution_type(support_resp)

        # Get intent if classifier available
        intent = None
        intent_confidence = None
        intent_source = "unlabeled"
        if intent_clf is not None:
            try:
                result = intent_clf.predict_with_confidence(pd.Series([customer_msg]))[0]
                intent = result["intent"]
                intent_confidence = result["confidence"]
                intent_source = "semantic_classifier"
            except Exception:
                pass

        # Normalize text
        customer_normalized = preprocess_text(customer_msg)
        support_normalized = preprocess_text(support_resp)

        # Build retrieval text
        context = build_conversation_context(
            df, col_map,
            pair.get("conversation_id", ""),
            pair.get("conversation_position", 0),
        )
        retrieval_text = build_retrieval_text(
            customer_msg, support_resp, resolution_type, context
        )

        # Create record
        kb_counter += 1
        record = KnowledgeRecord(
            knowledge_id=f"kb_{kb_counter:06d}",
            brand="selected_brand",
            conversation_id=pair.get("conversation_id"),
            source_message_id=pair.get("customer_message_id"),
            customer_message=customer_msg,
            support_response=support_resp,
            customer_message_normalized=customer_normalized,
            support_response_normalized=support_normalized,
            intent=intent,
            intent_confidence=intent_confidence,
            intent_source=intent_source,
            resolution_type=resolution_type,
            resolution_evidence=resolution_evidence,
            resolution_text=retrieval_text,
            conversation_position=pair.get("conversation_position", 0),
            has_followup=pair.get("has_followup", False),
            source_timestamp=None,
        )

        records.append(record.model_dump())

    print(f"Created {len(records):,} knowledge records")

    # Apply quality flags
    print("\nApplying quality flags...")
    duplicate_counts = detect_duplicates(records)
    for record in records:
        flags = apply_quality_flags(record)

        # Check for duplicates
        key = (
            record["customer_message"].strip().lower(),
            record["support_response"].strip().lower(),
        )
        if duplicate_counts.get(key, 0) > 1:
            flags.append("duplicate")

        record["quality_flags"] = flags
        record["quality_category"] = categorize_quality(flags)

    # Quality distribution
    quality_dist = {}
    for record in records:
        cat = record["quality_category"]
        quality_dist[cat] = quality_dist.get(cat, 0) + 1
    print(f"Quality distribution: {quality_dist}")

    # Resolution type distribution
    resolution_dist = {}
    for record in records:
        res = record["resolution_type"]
        resolution_dist[res] = resolution_dist.get(res, 0) + 1
    print(f"Resolution distribution: {resolution_dist}")

    # Save knowledge base
    output_config = config.get("output", {})
    kb_path = project_root / output_config.get("knowledge_base_path", "data/processed/knowledge_base.jsonl")
    kb_path.parent.mkdir(parents=True, exist_ok=True)

    with open(kb_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nKnowledge base saved to: {kb_path}")

    # Save metadata
    metadata = {
        "selected_brand": "selected_brand",
        "source": "Customer Support on Twitter",
        "source_rows": len(df),
        "conversations_processed": len(df.groupby(col_map.get("conversation_id", "text"))),
        "candidate_pairs": len(pairs),
        "final_records": len(records),
        "records_removed": len(pairs) - len(records),
        "quality_distribution": quality_dist,
        "resolution_distribution": resolution_dist,
        "intent_distribution": {},
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "preprocessing_version": "1.0",
        "classifier_model": intent_clf.embedding_model_name if intent_clf else None,
        "seed": args.seed,
    }

    # Intent distribution
    for record in records:
        intent = record.get("intent", "unlabeled")
        metadata["intent_distribution"][intent] = metadata["intent_distribution"].get(intent, 0) + 1

    metadata_path = project_root / output_config.get("metadata_path", "data/processed/knowledge_base_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Validate
    print("\nValidating knowledge base...")
    report = validate_knowledge_base(records)
    if report["valid"]:
        print("Validation PASSED")
    else:
        print(f"Validation FAILED with {len(report['errors'])} errors")
        for error in report["errors"][:5]:
            print(f"  - {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
