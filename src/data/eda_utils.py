"""Reusable EDA utility functions for the Hiver AI Support Agent project.

These functions provide consistent analysis across notebooks and scripts.
All functions work with the actual dataset schema - no assumed column names.

Usage:
    from src.data.eda_utils import summarize_dataframe, calculate_text_statistics
"""

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Schema detection
# ---------------------------------------------------------------------------

def detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Auto-detect key columns from the dataframe.

    Returns a dict mapping logical names to actual column names (or None).
    """
    col_map: dict[str, str | None] = {
        "text": None,
        "tweet_id": None,
        "conversation_id": None,
        "in_reply_to_tweet_id": None,
        "author_id": None,
        "author_name": None,
        "created_at": None,
        "brand": None,
        "inbound": None,
        "language": None,
    }

    text_candidates = ["text", "message", "content", "tweet_text"]
    for c in text_candidates:
        if c in df.columns:
            col_map["text"] = c
            break

    id_candidates = ["tweet_id", "id"]
    for c in id_candidates:
        if c in df.columns:
            col_map["tweet_id"] = c
            break

    conv_candidates = ["conversation_id", "thread_id"]
    for c in conv_candidates:
        if c in df.columns:
            col_map["conversation_id"] = c
            break

    reply_candidates = ["in_reply_to_tweet_id"]
    for c in reply_candidates:
        if c in df.columns:
            col_map["in_reply_to_tweet_id"] = c
            break

    author_candidates = ["author_id", "user_id"]
    for c in author_candidates:
        if c in df.columns:
            col_map["author_id"] = c
            break

    author_name_candidates = ["author_name", "inbound_author"]
    for c in author_name_candidates:
        if c in df.columns:
            col_map["author_name"] = c
            break

    time_candidates = ["created_at", "timestamp", "date"]
    for c in time_candidates:
        if c in df.columns:
            col_map["created_at"] = c
            break

    brand_candidates = ["brand", "company", "response_author"]
    for c in brand_candidates:
        if c in df.columns:
            col_map["brand"] = c
            break

    if "inbound" in df.columns:
        col_map["inbound"] = "inbound"

    lang_candidates = ["language", "lang"]
    for c in lang_candidates:
        if c in df.columns:
            col_map["language"] = c
            break

    return col_map


# ---------------------------------------------------------------------------
# Dataframe summary
# ---------------------------------------------------------------------------

def summarize_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return a high-level summary of a dataframe."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }


def summarize_missing_values(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Return missing-value counts and percentages per column."""
    n = len(df)
    result = {}
    for col in df.columns:
        count = int(df[col].isna().sum())
        result[col] = {
            "missing_count": count,
            "missing_pct": round(count / n * 100, 2) if n > 0 else 0.0,
        }
    return result


# ---------------------------------------------------------------------------
# Text statistics
# ---------------------------------------------------------------------------

def calculate_text_statistics(
    texts: pd.Series,
    label: str = "text",
) -> dict[str, Any]:
    """Compute text-level statistics for a Series of strings."""
    clean = texts.fillna("").astype(str)
    lengths = clean.str.len()
    word_counts = clean.str.split().str.len()

    return {
        "label": label,
        "count": len(texts),
        "empty_count": int((clean.str.strip() == "").sum()),
        "mean_char_length": round(float(lengths.mean()), 1),
        "median_char_length": round(float(lengths.median()), 1),
        "p75_char_length": round(float(lengths.quantile(0.75)), 1),
        "p90_char_length": round(float(lengths.quantile(0.90)), 1),
        "p95_char_length": round(float(lengths.quantile(0.95)), 1),
        "max_char_length": int(lengths.max()),
        "mean_word_count": round(float(word_counts.mean()), 1),
        "median_word_count": round(float(word_counts.median()), 1),
    }


# ---------------------------------------------------------------------------
# Conversation statistics
# ---------------------------------------------------------------------------

def calculate_conversation_statistics(
    df: pd.DataFrame,
    conv_col: str,
) -> dict[str, Any]:
    """Compute conversation-level statistics."""
    conv_lengths = df.groupby(conv_col).size()

    total = len(conv_lengths)
    single = int((conv_lengths == 1).sum())
    multi = total - single

    return {
        "unique_conversations": total,
        "mean_length": round(float(conv_lengths.mean()), 2),
        "median_length": round(float(conv_lengths.median()), 2),
        "p75_length": round(float(conv_lengths.quantile(0.75)), 2),
        "p90_length": round(float(conv_lengths.quantile(0.90)), 2),
        "p95_length": round(float(conv_lengths.quantile(0.95)), 2),
        "max_length": int(conv_lengths.max()),
        "single_message_count": single,
        "multi_message_count": multi,
        "single_message_pct": round(single / total * 100, 2) if total > 0 else 0.0,
        "multi_message_pct": round(multi / total * 100, 2) if total > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Brand statistics
# ---------------------------------------------------------------------------

def calculate_brand_statistics(
    df: pd.DataFrame,
    brand_col: str,
    conv_col: str | None = None,
) -> dict[str, Any]:
    """Compute brand-level statistics."""
    brand_msg_counts = df[brand_col].value_counts()
    stats: dict[str, Any] = {
        "unique_brands": int(brand_msg_counts.shape[0]),
        "top_brands": brand_msg_counts.head(20).to_dict(),
    }

    if conv_col and conv_col in df.columns:
        brand_conv = df.groupby(brand_col)[conv_col].nunique()
        stats["conversations_per_brand"] = brand_conv.to_dict()

    return stats


# ---------------------------------------------------------------------------
# Duplicate statistics
# ---------------------------------------------------------------------------

def calculate_duplicate_statistics(
    df: pd.DataFrame,
    text_col: str | None = None,
    id_col: str | None = None,
) -> dict[str, Any]:
    """Compute duplicate statistics."""
    stats: dict[str, Any] = {
        "exact_row_duplicates": int(df.duplicated().sum()),
        "exact_row_duplicate_pct": round(df.duplicated().mean() * 100, 2),
    }

    if id_col and id_col in df.columns:
        stats["duplicate_ids"] = int(df[id_col].duplicated().sum())
        stats["duplicate_id_pct"] = round(
            df[id_col].duplicated().mean() * 100, 2
        )

    if text_col and text_col in df.columns:
        stats["duplicate_texts"] = int(df[text_col].duplicated().sum())
        stats["duplicate_text_pct"] = round(
            df[text_col].duplicated().mean() * 100, 2
        )

    return stats


# ---------------------------------------------------------------------------
# Response time statistics
# ---------------------------------------------------------------------------

def calculate_response_time_statistics(
    df: pd.DataFrame,
    conv_col: str,
    time_col: str,
    inbound_col: str | None = None,
) -> dict[str, Any] | None:
    """Estimate response times within conversations.

    If inbound_col is available, measures time from first inbound to first
    non-inbound message in each conversation. Otherwise returns None.
    """
    if inbound_col is None or inbound_col not in df.columns:
        return None

    if time_col not in df.columns:
        return None

    df_copy = df.copy()
    try:
        df_copy["_parsed_time"] = pd.to_datetime(df_copy[time_col], errors="coerce")
    except Exception:
        return None

    valid = df_copy.dropna(subset=["_parsed_time"])
    if len(valid) == 0:
        return None

    # Find first inbound and first outbound per conversation
    inbound_mask = valid[inbound_col].astype(str).str.lower().isin(["true", "1", "yes"])
    inbound_df = valid[inbound_mask].copy()
    outbound_df = valid[~inbound_mask].copy()

    first_inbound = inbound_df.groupby(conv_col)["_parsed_time"].min()
    first_outbound = outbound_df.groupby(conv_col)["_parsed_time"].min()

    # Calculate response times
    common_convs = set(first_inbound.index) & set(first_outbound.index)
    if not common_convs:
        return None

    response_times = []
    for conv_id in common_convs:
        delta = first_outbound[conv_id] - first_inbound[conv_id]
        if delta.total_seconds() >= 0:
            response_times.append(delta.total_seconds())

    if not response_times:
        return None

    rt = pd.Series(response_times)

    return {
        "sample_size": len(response_times),
        "median_seconds": round(float(rt.median()), 1),
        "mean_seconds": round(float(rt.mean()), 1),
        "p75_seconds": round(float(rt.quantile(0.75)), 1),
        "p90_seconds": round(float(rt.quantile(0.90)), 1),
        "p95_seconds": round(float(rt.quantile(0.95)), 1),
        "min_seconds": round(float(rt.min()), 1),
        "max_seconds": round(float(rt.max()), 1),
    }


# ---------------------------------------------------------------------------
# Noise detection
# ---------------------------------------------------------------------------

URL_PATTERN = re.compile(r"https?://\S+|t\.co/\S+")
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#\w+")
REPEATED_PUNCT = re.compile(r"([!?.]){3,}")
ALL_CAPS_PATTERN = re.compile(r"\b[A-Z]{4,}\b")


def detect_noise_features(texts: pd.Series) -> dict[str, Any]:
    """Count prevalence of common noise features in text."""
    clean = texts.fillna("").astype(str)
    n = len(clean)

    has_url = clean.str.contains(URL_PATTERN, regex=True)
    has_mention = clean.str.contains(MENTION_PATTERN, regex=True)
    has_hashtag = clean.str.contains(HASHTAG_PATTERN, regex=True)
    has_repeated_punct = clean.str.contains(REPEATED_PUNCT, regex=True)
    is_all_caps = clean.str.contains(ALL_CAPS_PATTERN, regex=True)

    return {
        "url_pct": round(float(has_url.mean() * 100), 2),
        "mention_pct": round(float(has_mention.mean() * 100), 2),
        "hashtag_pct": round(float(has_hashtag.mean() * 100), 2),
        "repeated_punct_pct": round(float(has_repeated_punct.mean() * 100), 2),
        "all_caps_pct": round(float(is_all_caps.mean() * 100), 2),
    }
