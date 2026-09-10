# Golden Evaluation Set — Sampling Methodology

> **Status:** Template — will be populated after annotation.

---

## 1. Population

All customer messages from the selected brand's conversations in the development sample.

**Eligibility criteria:**
- Message is from a customer (not brand/support)
- Message has usable text content (not empty or whitespace-only)
- Message belongs to the selected brand

---

## 2. Exclusions

| Criteria | Reason |
|----------|--------|
| Empty text | Cannot label without content |
| Whitespace-only | No meaningful content |
| Brand/support messages | Not customer-initiated |
| Non-selected brand | Out of scope |

---

## 3. Sampling Unit

**Conversation-level separation** to prevent leakage.

The same conversation must NOT appear in both golden set and training/development data.

---

## 4. Stratification

**Strategy:** Stratified sampling to ensure representation.

**Categories:**
- Representative (normal messages)
- Short (< 20 chars)
- Difficult (long, complex)
- Noisy (URLs, mentions, hashtags)
- Confusable (near intent boundaries)

**Target distribution:**
- 70% representative
- 10% short
- 10% difficult
- 10% noisy

---

## 5. Difficult Examples

Deliberately included:
- Very short messages
- Messages with spelling errors
- Messages with multiple issues
- Messages near confusable intent boundaries
- Messages with unusual phrasing

---

## 6. Random Seed

**Seed:** 42 (from project configuration)

Ensures reproducibility of sampling.

---

## 7. Final Size

**Target:** 200 examples

**Range:** 150-250 examples

---

## 8. Leakage Prevention

Checks performed:
- Conversation ID overlap with development data
- Message ID overlap with development data
- Exact text overlap with development data

---

## 9. Human Labeling

**Method:** Single-annotator labeling with structured second-pass self-review.

**Process:**
1. View customer message and context
2. Select primary intent from taxonomy
3. Mark confidence level
4. Add notes for difficult cases
5. Second-pass review of LOW confidence and ambiguous examples

---

## 10. Limitations

1. **Sampling bias** — candidate pool may not perfectly represent all message types
2. **Annotation subjectivity** — some intent boundaries are inherently subjective
3. **Rare intents** — some intents may have fewer examples
4. **Inferred labels** — labels are based on message content, not ground-truth customer intent
5. **Dataset noise** — social-media text contains noise that may affect labeling
