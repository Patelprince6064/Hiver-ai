"""Create final evaluation manifest.

Generates deterministic synthetic evaluation data for Phase 18.
"""

import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_final_manifest(seed: int = 42) -> list[dict]:
    """Create final evaluation manifest with synthetic data."""
    rng = random.Random(seed)
    
    # Define intent categories with realistic distribution
    intent_templates = {
        "order_status": [
            "Where is my order?",
            "When will my order arrive?",
            "Can you check my order status?",
            "I haven't received my order yet.",
            "My order is late.",
            "How do I track my order?",
            "Order number {id} - where is it?",
            "Still waiting for my package.",
        ],
        "return": [
            "I want to return this item.",
            "How do I start a return?",
            "This product is defective, I need to return it.",
            "Can I return an item without the original packaging?",
            "What's your return policy?",
            "I need to return something I bought.",
            "Return request for order {id}.",
            "Item doesn't match description, want to return.",
        ],
        "refund": [
            "I need a refund.",
            "When will I get my refund?",
            "Can I get a refund for this?",
            "My refund hasn't arrived yet.",
            "I want my money back.",
            "Refund for cancelled order {id}.",
            "How long do refunds take?",
            "Refund not processed yet.",
        ],
        "account": [
            "How do I reset my password?",
            "I can't log into my account.",
            "Update my email address.",
            "Change my account settings.",
            "I need to verify my identity.",
            "My account was locked.",
            "Update my billing information.",
            "How do I delete my account?",
        ],
        "technical_support": [
            "The app isn't working.",
            "I'm having technical issues.",
            "Website keeps crashing.",
            "Can't load the page.",
            "Error message when checkout.",
            "App won't open.",
            "Login page broken.",
            "Payment processing error.",
        ],
        "product_inquiry": [
            "Do you have this in stock?",
            "What colors are available?",
            "Is this item available?",
            "Product specifications?",
            "When will this be restocked?",
            "Do you sell gift cards?",
            "What's the price for bulk orders?",
            "Is there a warranty?",
        ],
        "shipping": [
            "How much is shipping?",
            "Do you ship internationally?",
            "Can I change my shipping address?",
            "Expedited shipping options?",
            "Shipping cost seems wrong.",
            "Free shipping threshold?",
            "My package was lost.",
            "Delivery to P.O. box?",
        ],
        "complaint": [
            "I'm very unhappy with your service.",
            "This is unacceptable.",
            "Worst customer service ever.",
            "I want to speak to a manager.",
            "Very disappointed.",
            "Your service has been terrible.",
            "I need to file a complaint.",
            "This needs to be resolved immediately.",
        ],
        "billing": [
            "I was charged twice.",
            "Wrong amount charged.",
            "My payment failed.",
            "Update my credit card.",
            "Promo code not working.",
            "I have a billing question.",
            "Invoice discrepancy.",
            "Need to change payment method.",
        ],
        "general_inquiry": [
            "What are your business hours?",
            "How do I contact support?",
            "Do you have a physical store?",
            "What's your email?",
            "Can I speak to someone?",
            "How do I apply for a job?",
            "Do you offer gift wrapping?",
            "What payment methods do you accept?",
        ],
    }
    
    # Difficulty levels
    difficulties = ["easy", "medium", "hard"]
    difficulty_weights = [0.4, 0.4, 0.2]
    
    # Ambiguity levels
    ambiguity_levels = ["clear", "somewhat_ambiguous", "very_ambiguous"]
    ambiguity_weights = [0.6, 0.3, 0.1]
    
    manifest = []
    
    # Generate 200 examples
    for i in range(200):
        intent = rng.choice(list(intent_templates.keys()))
        template = rng.choice(intent_templates[intent])
        
        # Add some variation
        message = template.format(id=f"ORD-{rng.randint(10000, 99999)}")
        
        # Add noise to some messages
        if rng.random() < 0.1:
            noise_words = ["please", "thanks", "urgent", "help"]
            message = f"{rng.choice(noise_words)} {message}"
        
        # Truncate some messages
        if rng.random() < 0.05:
            message = message[:20]
        
        difficulty = rng.choices(difficulties, weights=difficulty_weights)[0]
        ambiguity = rng.choices(ambiguity_levels, weights=ambiguity_weights)[0]
        
        # Simulate ground truth labels
        should_escalate = False
        escalation_reasons = []
        
        # High-risk intents more likely to escalate
        if intent in ["refund", "account", "billing"]:
            if rng.random() < 0.3:
                should_escalate = True
                escalation_reasons.append("ACCOUNT_ACTION_REQUIRED")
        
        # Harder messages more likely to escalate
        if difficulty == "hard":
            if rng.random() < 0.4:
                should_escalate = True
                escalation_reasons.append("LOW_INTENT_CONFIDENCE")
        
        # Very ambiguous messages escalate
        if ambiguity == "very_ambiguous":
            if rng.random() < 0.5:
                should_escalate = True
                escalation_reasons.append("AMBIGUOUS_REQUEST")
        
        # Add retrieval-related features
        has_evidence = rng.random() < 0.7
        retrieval_score = rng.uniform(0.3, 0.95) if has_evidence else 0.0
        
        # Add grounding features
        grounding_pass = has_evidence and rng.random() < 0.8
        has_unsupported_claims = not grounding_pass and rng.random() < 0.3
        
        record = {
            "id": f"eval_{i+1:04d}",
            "message": message,
            "conversation_id": f"conv_eval_{i+1:04d}",
            "message_id": f"msg_eval_{i+1:04d}",
            "intent": intent,
            "difficulty": difficulty,
            "ambiguity": ambiguity,
            "has_evidence": has_evidence,
            "retrieval_score": round(retrieval_score, 3),
            "grounding_pass": grounding_pass,
            "has_unsupported_claims": has_unsupported_claims,
            "should_escalate": should_escalate,
            "escalation_reasons": escalation_reasons,
        }
        
        manifest.append(record)
    
    return manifest


def main() -> None:
    """Create and save final evaluation manifest."""
    output_dir = PROJECT_ROOT / "data" / "interim" / "final_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = create_final_manifest(seed=42)
    
    # Save manifest
    manifest_path = output_dir / "final_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for record in manifest:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Save metadata
    metadata = {
        "description": "Final evaluation manifest for Phase 18",
        "created_at": "2026-09-10",
        "seed": 42,
        "total_examples": len(manifest),
        "intent_distribution": {},
        "difficulty_distribution": {},
        "ambiguity_distribution": {},
        "escalation_rate": 0.0,
        "evidence_coverage_rate": 0.0,
        "grounding_pass_rate": 0.0,
    }
    
    # Calculate distributions
    intents = [r["intent"] for r in manifest]
    difficulties = [r["difficulty"] for r in manifest]
    ambiguities = [r["ambiguity"] for r in manifest]
    escalations = [r["should_escalate"] for r in manifest]
    evidence = [r["has_evidence"] for r in manifest]
    grounding = [r["grounding_pass"] for r in manifest]
    
    from collections import Counter
    
    metadata["intent_distribution"] = dict(Counter(intents))
    metadata["difficulty_distribution"] = dict(Counter(difficulties))
    metadata["ambiguity_distribution"] = dict(Counter(ambiguities))
    metadata["escalation_rate"] = sum(escalations) / len(escalations)
    metadata["evidence_coverage_rate"] = sum(evidence) / len(evidence)
    metadata["grounding_pass_rate"] = sum(grounding) / len(grounding)
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Created final evaluation manifest: {len(manifest)} examples")
    print(f"Saved to: {manifest_path}")
    print(f"Metadata saved to: {metadata_path}")
    print(f"\nIntent distribution: {metadata['intent_distribution']}")
    print(f"Difficulty distribution: {metadata['difficulty_distribution']}")
    print(f"Escalation rate: {metadata['escalation_rate']:.1%}")


if __name__ == "__main__":
    main()
