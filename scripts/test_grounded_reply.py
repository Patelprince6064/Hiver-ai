#!/usr/bin/env python3
"""Test the grounded reply generator with a single query.

Usage:
    python scripts/test_grounded_reply.py --query "My order has not arrived yet." --mock
    python scripts/test_grounded_reply.py --query "My order has not arrived yet."
"""

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config() -> dict:
    with open(PROJECT_ROOT / "configs" / "generation.yaml", "r") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test grounded reply generator")
    parser.add_argument("--query", required=True, help="Customer message to test")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM provider")
    parser.add_argument("--intent", default=None, help="Override predicted intent")
    args = parser.parse_args()

    config = load_config()
    llm_config = config["generation"].get("grounded_llm", {})

    print("=" * 60)
    print("PHASE 12 — GROUNDED REPLY GENERATOR TEST")
    print("=" * 60)

    # Check prerequisites
    index_dir = PROJECT_ROOT / "data" / "processed" / "retrieval_index"
    if not (index_dir / "index.faiss").exists():
        print(f"\nError: Retrieval index not found at {index_dir}")
        print("Run: python scripts/build_retrieval_index.py")
        return 1

    # Initialize retriever
    print("\nLoading retrieval index...")
    from src.retrieval.retriever import HistoricalSupportRetriever
    retriever = HistoricalSupportRetriever()
    retriever.load(index_dir)
    print("Retriever loaded.")

    # Initialize LLM provider
    if args.mock:
        from src.generation.llm.mock_provider import MockLLMProvider
        llm_provider = MockLLMProvider(
            response="Sorry about the delay. Please DM us your order number so we can check the status of your order."
        )
        print("Using mock LLM provider.")
    else:
        from src.generation.llm.openai_provider import OpenAIProvider
        try:
            llm_provider = OpenAIProvider(
                model=llm_config.get("model", "gpt-4o-mini"),
                timeout=llm_config.get("timeout", 30),
                max_retries=llm_config.get("max_retries", 1),
            )
            print(f"Using OpenAI provider: {llm_config.get('model', 'gpt-4o-mini')}")
        except Exception as e:
            print(f"Error initializing OpenAI provider: {e}")
            print("Use --mock for testing without API credentials.")
            return 1

    # Initialize generator
    from src.generation.grounded_reply_generator import GroundedReplyGenerator
    from src.generation.evidence_selector import EvidenceSelector
    from src.generation.context_budget import ContextBudget

    generator = GroundedReplyGenerator(
        retriever=retriever,
        llm_provider=llm_provider,
        evidence_selector=EvidenceSelector(
            max_evidence=llm_config.get("evidence_top_k", 3),
            min_similarity=llm_config.get("min_similarity"),
            deduplicate=llm_config.get("deduplicate_evidence", True),
        ),
        context_budget=ContextBudget(
            max_customer_message_chars=llm_config.get("context_budget", {}).get("max_customer_message_chars", 500),
            max_evidence_item_chars=llm_config.get("context_budget", {}).get("max_evidence_item_chars", 300),
            max_total_evidence_chars=llm_config.get("context_budget", {}).get("max_total_evidence_chars", 1500),
        ),
        temperature=llm_config.get("temperature", 0.0),
        max_tokens=llm_config.get("max_tokens", 300),
        prompt_version=llm_config.get("prompt_version", "v1"),
    )

    # Predict intent
    intent = args.intent
    confidence = None
    if intent is None:
        try:
            from src.intents.semantic_classifier import SemanticIntentClassifier
            clf = SemanticIntentClassifier.load(PROJECT_ROOT / "models" / "semantic_classifier")
            import pandas as pd
            result = clf.predict_with_confidence(pd.Series([args.query]))[0]
            intent = result["intent"]
            confidence = result["confidence"]
        except Exception:
            intent = "unknown"
            confidence = None

    # Generate reply
    print(f"\nGenerating reply for: {args.query}")
    start = time.time()
    output = generator.generate(
        customer_message=args.query,
        predicted_intent=intent,
        intent_confidence=confidence,
    )
    elapsed = (time.time() - start) * 1000

    # Display results
    print(f"\n{'=' * 60}")
    print("CUSTOMER")
    print(f"{'=' * 60}")
    print(args.query)

    print(f"\n{'=' * 60}")
    print("INTENT")
    print(f"{'=' * 60}")
    print(f"{intent}")
    if confidence is not None:
        print(f"Confidence: {confidence:.2f}")

    print(f"\n{'=' * 60}")
    print("RETRIEVED EVIDENCE")
    print(f"{'=' * 60}")
    for i, ev in enumerate(output.evidence, 1):
        print(f"\n{i}. Similarity: {ev.similarity_score:.2f}")
        if ev.intent:
            print(f"   Intent: {ev.intent}")
        if ev.resolution_type:
            print(f"   Resolution: {ev.resolution_type}")
        print(f"   Support Response: {ev.support_response[:120]}...")

    print(f"\n{'=' * 60}")
    print("GENERATED REPLY")
    print(f"{'=' * 60}")
    if output.reply:
        print(output.reply)
    else:
        print("[No reply generated]")

    print(f"\n{'=' * 60}")
    print("STATUS")
    print(f"{'=' * 60}")
    print(f"Status: {output.status}")
    print(f"Method: {output.generation_method}")
    print(f"Latency: {elapsed:.0f}ms")
    if output.metadata.get("usage"):
        print(f"Usage: {output.metadata['usage']}")
    if output.risk_flags:
        print(f"Risk flags: {output.risk_flags}")

    print(f"\n{'=' * 60}")
    print("TEST COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
