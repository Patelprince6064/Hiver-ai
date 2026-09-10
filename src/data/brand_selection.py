"""Brand selection scoring model for the Hiver AI Support Agent.

This module implements a transparent, reproducible scoring methodology
for selecting the most suitable brand from the Customer Support on Twitter
dataset.

The scoring is based on DATA SUITABILITY only — not model performance.
This avoids circular selection and ensures the choice is made before
any model development.

Scoring Dimensions:
    A. Conversation volume (0.20)
    B. Multi-turn coverage (0.20)
    C. Support-response coverage (0.20)
    D. Conversation quality (0.15)
    E. Customer-support density (0.10)
    F. Issue diversity proxy (0.10)
    G. Evaluation suitability (0.05)
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "conversation_volume": 0.20,
    "multi_turn_coverage": 0.20,
    "support_response_coverage": 0.20,
    "conversation_quality": 0.15,
    "customer_support_density": 0.10,
    "issue_diversity_proxy": 0.10,
    "evaluation_suitability": 0.05,
}


@dataclass
class BrandScore:
    """A single brand's scoring result."""

    brand: str
    conversation_volume: float = 0.0
    multi_turn_coverage: float = 0.0
    support_response_coverage: float = 0.0
    conversation_quality: float = 0.0
    customer_support_density: float = 0.0
    issue_diversity_proxy: float = 0.0
    evaluation_suitability: float = 0.0
    total_score: float = 0.0

    # Raw values for reporting
    raw_conversations: int = 0
    raw_messages: int = 0
    raw_multi_turn_pct: float = 0.0
    raw_response_coverage: float = 0.0
    raw_customer_messages: int = 0
    raw_support_messages: int = 0


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def min_max_normalize(values: list[float]) -> list[float]:
    """Min-max normalize a list of values to [0, 1].

    Handles the case where max == min (all values identical) by returning 0.5.
    """
    if not values:
        return []

    arr = np.array(values, dtype=float)
    min_val = arr.min()
    max_val = arr.max()

    if max_val == min_val:
        return [0.5] * len(values)

    return ((arr - min_val) / (max_val - min_val)).tolist()


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def compute_brand_features(
    df: pd.DataFrame,
    brand_col: str,
    conv_col: str,
    text_col: str,
    inbound_col: str | None = None,
) -> list[dict[str, Any]]:
    """Compute raw features for each brand.

    Returns a list of dicts, one per brand, with raw metric values.
    """
    features = []

    for brand, group in df.groupby(brand_col):
        n_convs = group[conv_col].nunique()
        n_msgs = len(group)

        # Conversation length distribution
        conv_sizes = group.groupby(conv_col).size()
        n_multi = int((conv_sizes > 1).sum())
        multi_pct = (n_multi / n_convs * 100) if n_convs > 0 else 0.0

        # Customer vs support
        n_customer = 0
        n_support = 0
        convs_with_support = 0

        if inbound_col and inbound_col in group.columns:
            inbound_mask = group[inbound_col].astype(str).str.lower().isin(["true", "1", "yes"])
            n_customer = int(inbound_mask.sum())
            n_support = int((~inbound_mask).sum())
            convs_with_support = group[~inbound_mask].groupby(conv_col).ngroups
        else:
            # Fallback: assume roughly half are customer messages
            n_customer = n_msgs // 2
            n_support = n_msgs - n_customer
            convs_with_support = n_convs  # Assume all have support

        response_coverage = (convs_with_support / n_convs * 100) if n_convs > 0 else 0.0

        # Customer-support density: ratio of customer+support messages to total
        # (higher is better — means more actual support interactions)
        cs_density = ((n_customer + n_support) / n_msgs * 100) if n_msgs > 0 else 0.0

        # Text diversity proxy: unique words per message (rough)
        if text_col and text_col in group.columns:
            sample_size = min(500, len(group))
            sample_texts = group[text_col].dropna().astype(str).sample(
                n=sample_size, random_state=42
            ) if len(group) > 0 else pd.Series([])
            if len(sample_texts) > 0:
                all_words = " ".join(sample_texts).lower().split()
                unique_words = len(set(all_words))
                avg_words = len(all_words) / len(sample_texts) if len(sample_texts) > 0 else 0
                diversity_proxy = unique_words / max(avg_words, 1)
            else:
                diversity_proxy = 0.0
        else:
            diversity_proxy = 0.0

        # Conversation quality: estimate based on multi-turn and response coverage
        # (higher multi-turn % and higher response coverage = better quality)
        quality = (multi_pct * 0.5 + response_coverage * 0.5) / 100

        # Evaluation suitability: enough data for train/val/test + golden set
        # Minimum: ~50 conversations for golden set, ~200 for training
        eval_suitable = min(n_convs / 200, 1.0)  # Cap at 1.0

        features.append({
            "brand": brand,
            "raw_conversations": n_convs,
            "raw_messages": n_msgs,
            "raw_multi_turn_pct": round(multi_pct, 2),
            "raw_response_coverage": round(response_coverage, 2),
            "raw_customer_messages": n_customer,
            "raw_support_messages": n_support,
            "raw_cs_density": round(cs_density, 2),
            "raw_diversity_proxy": round(diversity_proxy, 4),
            "raw_quality": round(quality, 4),
            "raw_eval_suitable": round(eval_suitable, 4),
        })

    return features


def score_brands(
    features: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> list[BrandScore]:
    """Score and rank brands based on computed features.

    Args:
        features: Raw feature dicts from compute_brand_features().
        weights: Optional custom weights. Uses DEFAULT_WEIGHTS if None.

    Returns:
        List of BrandScore objects sorted by total_score (descending).
    """
    if not features:
        return []

    weights = weights or DEFAULT_WEIGHTS

    # Extract raw values for normalization
    conv_volumes = [f["raw_conversations"] for f in features]
    multi_pcts = [f["raw_multi_turn_pct"] for f in features]
    response_covs = [f["raw_response_coverage"] for f in features]
    qualities = [f["raw_quality"] for f in features]
    cs_densities = [f["raw_cs_density"] for f in features]
    diversities = [f["raw_diversity_proxy"] for f in features]
    eval_suites = [f["raw_eval_suitable"] for f in features]

    # Normalize each dimension
    norm_conv = min_max_normalize(conv_volumes)
    norm_multi = min_max_normalize(multi_pcts)
    norm_resp = min_max_normalize(response_covs)
    norm_quality = min_max_normalize(qualities)
    norm_density = min_max_normalize(cs_densities)
    norm_diversity = min_max_normalize(diversities)
    norm_eval = min_max_normalize(eval_suites)

    # Compute weighted scores
    scores = []
    for i, f in enumerate(features):
        components = {
            "conversation_volume": norm_conv[i],
            "multi_turn_coverage": norm_multi[i],
            "support_response_coverage": norm_resp[i],
            "conversation_quality": norm_quality[i],
            "customer_support_density": norm_density[i],
            "issue_diversity_proxy": norm_diversity[i],
            "evaluation_suitability": norm_eval[i],
        }

        total = sum(components[k] * weights.get(k, 0) for k in components)

        score = BrandScore(
            brand=f["brand"],
            conversation_volume=round(components["conversation_volume"], 4),
            multi_turn_coverage=round(components["multi_turn_coverage"], 4),
            support_response_coverage=round(components["support_response_coverage"], 4),
            conversation_quality=round(components["conversation_quality"], 4),
            customer_support_density=round(components["customer_support_density"], 4),
            issue_diversity_proxy=round(components["issue_diversity_proxy"], 4),
            evaluation_suitability=round(components["evaluation_suitability"], 4),
            total_score=round(total, 4),
            raw_conversations=f["raw_conversations"],
            raw_messages=f["raw_messages"],
            raw_multi_turn_pct=f["raw_multi_turn_pct"],
            raw_response_coverage=f["raw_response_coverage"],
            raw_customer_messages=f["raw_customer_messages"],
            raw_support_messages=f["raw_support_messages"],
        )
        scores.append(score)

    # Sort by total score descending
    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores


def select_brand(
    df: pd.DataFrame,
    brand_col: str,
    conv_col: str,
    text_col: str,
    inbound_col: str | None = None,
    weights: dict[str, float] | None = None,
    min_conversations: int = 50,
) -> tuple[BrandScore, list[BrandScore]]:
    """End-to-end brand selection from a dataframe.

    Returns:
        Tuple of (selected_brand_score, all_scores).
    """
    features = compute_brand_features(df, brand_col, conv_col, text_col, inbound_col)
    all_scores = score_brands(features, weights)

    # Filter by minimum conversation threshold
    suitable = [s for s in all_scores if s.raw_conversations >= min_conversations]

    if not suitable:
        # Fall back to highest scoring brand regardless of threshold
        suitable = all_scores[:1] if all_scores else []

    selected = suitable[0] if suitable else None
    return selected, all_scores
