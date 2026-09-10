"""Response pairing for knowledge base construction.

Pairs customer messages with support responses from historical conversations.
"""

from typing import Any

import pandas as pd


def identify_customer_messages(df: pd.DataFrame, col_map: dict) -> pd.Series:
    """Identify customer messages from the dataset."""
    author_col = col_map.get("author")
    if author_col and author_col in df.columns:
        # Use author information if available
        return df[author_col].astype(str).str.lower().str.contains(
            r"customer|user|person|individual", regex=True, na=False
        )
    else:
        # Fallback: assume first message in conversation is customer
        return pd.Series(True, index=df.index)


def identify_support_messages(df: pd.DataFrame, col_map: dict) -> pd.Series:
    """Identify support/brand messages from the dataset."""
    author_col = col_map.get("author")
    if author_col and author_col in df.columns:
        # Use author information if available
        return df[author_col].astype(str).str.lower().str.contains(
            r"brand|support|company|agent|official", regex=True, na=False
        )
    else:
        # Fallback: assume alternating pattern
        return pd.Series(False, index=df.index)


def pair_customer_support_messages(
    df: pd.DataFrame,
    col_map: dict,
) -> list[dict[str, Any]]:
    """Pair customer messages with support responses.

    Returns list of paired records with customer/support messages.
    """
    pairs = []

    conv_col = col_map.get("conversation_id")
    text_col = col_map.get("text")
    author_col = col_map.get("author")
    id_col = col_map.get("tweet_id")

    if not conv_col or not text_col:
        return pairs

    # Sort by conversation and timestamp
    sort_cols = [conv_col]
    time_col = col_map.get("timestamp")
    if time_col and time_col in df.columns:
        sort_cols.append(time_col)

    df_sorted = df.sort_values(sort_cols).copy()

    # Group by conversation
    for conv_id, group in df_sorted.groupby(conv_col):
        messages = group.to_dict("records")
        if len(messages) < 2:
            continue

        # Find customer-support pairs
        customer_msg = None
        customer_idx = None

        for i, msg in enumerate(messages):
            text = msg.get(text_col, "")

            # Determine if customer or support
            is_customer = True
            if author_col and author_col in msg:
                author = str(msg[author_col]).lower()
                if any(kw in author for kw in ["brand", "support", "company", "agent", "official"]):
                    is_customer = False

            if is_customer:
                # Start of a new customer message
                customer_msg = msg
                customer_idx = i
            else:
                # Support response - pair with previous customer message
                if customer_msg is not None:
                    record = {
                        "conversation_id": str(conv_id),
                        "customer_message": str(customer_msg.get(text_col, "")),
                        "support_response": str(msg.get(text_col, "")),
                        "customer_message_id": str(customer_msg.get(id_col, "")) if id_col else None,
                        "support_message_id": str(msg.get(id_col, "")) if id_col else None,
                        "conversation_position": customer_idx,
                        "has_followup": i < len(messages) - 1,
                    }
                    pairs.append(record)
                    customer_msg = None

    return pairs


def build_conversation_context(
    df: pd.DataFrame,
    col_map: dict,
    target_conv_id: str,
    target_position: int,
    max_context: int = 3,
) -> str:
    """Build compact context before a support response."""
    conv_col = col_map.get("conversation_id")
    text_col = col_map.get("text")

    if not conv_col or not text_col:
        return ""

    conversation = df[df[conv_col] == target_conv_id].sort_values(
        by=[col_map.get("timestamp", text_col)] if col_map.get("timestamp") else [text_col]
    )

    context_messages = []
    for _, row in conversation.iterrows():
        pos = row.name
        if pos >= target_position:
            break
        context_messages.append(str(row[text_col]))

    # Take last N messages
    context_messages = context_messages[-max_context:]
    return "\n".join(context_messages)
