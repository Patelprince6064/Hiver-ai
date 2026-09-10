"""Message extraction utilities for intent discovery.

This module provides reusable functions for:
- Loading selected-brand data
- Identifying customer vs support messages
- Extracting usable customer messages
- Preparing intent-discovery datasets

All functions work with the actual dataset schema — no assumed column names.
"""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.data.eda_utils import detect_columns


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_selected_brand_data(
    selected_brand_dir: Path,
) -> pd.DataFrame | None:
    """Load the selected brand's messages from data/interim/selected_brand/."""
    messages_path = selected_brand_dir / "messages.csv"
    if not messages_path.exists():
        return None
    return pd.read_csv(messages_path, low_memory=False)


# ---------------------------------------------------------------------------
# Customer vs Support identification
# ---------------------------------------------------------------------------

def identify_customer_messages(
    df: pd.DataFrame,
    col_map: dict[str, str | None],
) -> pd.Series:
    """Create a boolean mask for customer messages.

    Uses the strongest available signal:
    1. 'inbound' column (True = customer)
    2. 'author_type' column (if available)
    3. Heuristic fallback
    """
    inbound_col = col_map.get("inbound")

    if inbound_col and inbound_col in df.columns:
        return df[inbound_col].astype(str).str.lower().isin(["true", "1", "yes"])

    # Fallback: check for other signals
    for col in df.columns:
        if "inbound" in col.lower() or "customer" in col.lower():
            if df[col].dtype == bool:
                return df[col]
            return df[col].astype(str).str.lower().isin(["true", "1", "yes"])

    # Last resort: assume ~half are customer messages
    # (not ideal, but allows the pipeline to proceed)
    return pd.Series([False] * len(df), index=df.index)


def identify_support_messages(
    df: pd.DataFrame,
    col_map: dict[str, str | None],
) -> pd.Series:
    """Create a boolean mask for support/brand messages."""
    return ~identify_customer_messages(df, col_map)


# ---------------------------------------------------------------------------
# Message filtering
# ---------------------------------------------------------------------------

def filter_usable_messages(
    df: pd.DataFrame,
    text_col: str,
    min_length: int = 2,
) -> pd.DataFrame:
    """Filter to messages with usable text content.

    Excludes:
    - Empty or whitespace-only text
    - Extremely short messages (configurable)
    - Messages with no meaningful content

    Does NOT aggressively clean social-media text.
    """
    if text_col not in df.columns:
        return df

    # Create mask for usable messages
    text_series = df[text_col].fillna("").astype(str)
    is_usable = (
        (text_series.str.strip().str.len() >= min_length)
        & (text_series.str.strip() != "")
    )

    return df[is_usable].copy()


# ---------------------------------------------------------------------------
# Text normalization (preserving original)
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize text while preserving meaning.

    Applies:
    - Lowercase
    - Whitespace normalization
    - URL placeholder
    - Mention placeholder

    Does NOT remove:
    - Emojis
    - Punctuation (except URLs/mentions)
    - Slang or informal language
    """
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"https?://\S+|t\.co/\S+", "[URL]", text)
    text = re.sub(r"@\w+", "[MENTION]", text)
    return text


# ---------------------------------------------------------------------------
# Intent discovery dataset creation
# ---------------------------------------------------------------------------

def create_intent_discovery_dataset(
    df: pd.DataFrame,
    col_map: dict[str, str | None],
    text_col: str,
    sample_size: int | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a dataset for intent discovery.

    Steps:
    1. Filter to customer messages
    2. Filter to usable messages
    3. Add normalized text
    4. Optionally sample
    """
    # Identify customer messages
    customer_mask = identify_customer_messages(df, col_map)
    customer_df = df[customer_mask].copy()

    # Filter to usable messages
    filtered_df = filter_usable_messages(customer_df, text_col)

    # Add normalized text
    filtered_df["normalized_text"] = filtered_df[text_col].apply(normalize_text)

    # Add message metadata
    conv_col = col_map.get("conversation_id")
    time_col = col_map.get("created_at")
    id_col = col_map.get("tweet_id")

    if conv_col and conv_col in filtered_df.columns:
        filtered_df["conversation_id"] = filtered_df[conv_col]

    if time_col and time_col in filtered_df.columns:
        filtered_df["timestamp"] = filtered_df[time_col]

    if id_col and id_col in filtered_df.columns:
        filtered_df["message_id"] = filtered_df[id_col]

    # Sample if requested
    if sample_size and len(filtered_df) > sample_size:
        filtered_df = filtered_df.sample(n=sample_size, random_state=seed)

    return filtered_df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Text quality analysis
# ---------------------------------------------------------------------------

def analyze_text_quality(
    df: pd.DataFrame,
    text_col: str,
) -> dict[str, Any]:
    """Analyze text quality of messages."""
    if text_col not in df.columns:
        return {}

    texts = df[text_col].fillna("").astype(str)

    return {
        "total_messages": len(texts),
        "empty_messages": int((texts.str.strip() == "").sum()),
        "very_short": int((texts.str.len() < 5).sum()),
        "short": int((texts.str.len() < 20).sum()),
        "medium": int(((texts.str.len() >= 20) & (texts.str.len() < 100)).sum()),
        "long": int((texts.str.len() >= 100).sum()),
        "mean_length": round(float(texts.str.len().mean()), 1),
        "median_length": round(float(texts.str.len().median()), 1),
    }
