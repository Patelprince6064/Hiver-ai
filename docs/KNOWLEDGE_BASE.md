# Knowledge Base

## Purpose

Historical evidence store for support-response retrieval. Contains customer-support message pairs from the selected brand's historical conversations.

## Record Structure

Each knowledge record contains:

| Field | Description |
|-------|-------------|
| `knowledge_id` | Unique identifier |
| `brand` | Brand name |
| `conversation_id` | Source conversation |
| `customer_message` | Original customer text |
| `support_response` | Original support text |
| `intent` | Predicted intent (if available) |
| `intent_confidence` | Prediction confidence |
| `intent_source` | Source of intent prediction |
| `resolution_type` | Historical response category |
| `resolution_evidence` | Evidence for resolution type |
| `retrieval_text` | Canonical text for embedding |
| `quality_flags` | Quality indicators |
| `quality_category` | usable/usable_with_context/low_quality |

## Provenance

Every record maps to a real source conversation and message. No synthetic data is generated.

## Resolution Taxonomy

Historical response categories (not business policies):

- `information_provided` — Support provided information
- `troubleshooting` — Suggested troubleshooting steps
- `requested_information` — Asked for more details
- `requested_private_contact` — Asked to DM or contact privately
- `status_update` — Provided status update
- `refund_or_compensation_discussion` — Discussed refund/compensation
- `replacement_or_rebooking_discussion` — Discussed replacement
- `escalated` — Escalated to team/specialist
- `apology_only` — Only apologized
- `unclear` — Resolution unclear
- `no_resolution` — No response visible
- `other` — Other actions

## Quality Filtering

Records are flagged for quality issues:

- Empty messages
- Very short messages
- Missing conversation IDs
- Unclear resolution
- High noise (URLs, mentions)
- Duplicates

Quality categories:
- `usable` — No quality issues
- `usable_with_context` — Minor issues, usable with context
- `low_quality` — Significant quality issues

## Intent Attachment

Intents are model predictions from the semantic classifier. They are NOT ground truth.

- `intent_source = semantic_classifier` — Predicted by model
- `intent_source = unlabeled` — No prediction available

## Leakage Prevention

Golden set conversations are excluded from the knowledge base.

## Known Limitations

- Historical support responses may be outdated
- Responses may be inconsistent across agents
- Some threads are incomplete
- Twitter conversations are noisy
- Visible conversation may not contain final resolution
- Response does not necessarily represent official policy
- Intent predictions may be incorrect
