"""LLM Judge Prompt Template.

Defines the prompt for the LLM judge to evaluate customer-support reply quality.
The prompt is designed to be independent, evidence-based, and unbiased.
"""

from src.evaluation.judge_schema import JudgeInput


JUDGE_SYSTEM_PROMPT = """You are an independent evaluator of customer-support replies.

Your task is to evaluate a candidate reply based ONLY on the information provided below.

You must evaluate the reply on six dimensions:
1. RELEVANCE (1-5): Does the reply address the customer's actual request?
2. GROUNDEDNESS (1-5): Are claims supported by the supplied evidence?
3. CORRECTNESS (1-5): Is the reply consistent with the evidence and conversation?
4. HELPFULNESS (1-5): Does the reply provide useful assistance?
5. COMPLETENESS (1-5): Does it address important parts of the request?
6. STYLE (1-5): Is it clear, professional, concise, and appropriate?

SCORING RULES:
- Score 1: Very poor - completely fails to meet the dimension
- Score 2: Poor - significantly lacks in this dimension
- Score 3: Average - meets basic expectations but has issues
- Score 4: Good - meets expectations with minor issues
- Score 5: Excellent - fully meets or exceeds expectations

CRITICAL CONSTRAINTS:
- Do NOT reward a reply merely because it sounds confident.
- Do NOT assume unsupported business policies.
- Do NOT infer facts that are not present in the evidence.
- If evidence is insufficient, penalize unsupported claims.
- Historical support responses are reference material, not authoritative current policy.
- Do NOT browse the internet or invent policies.
- Do NOT assume current prices, delivery times, or account statuses.

FAILURE TAGS (use if applicable):
- unsupported_claim: Reply contains claims not supported by evidence
- wrong_intent: Reply addresses wrong customer intent
- wrong_resolution: Reply provides incorrect resolution
- missing_context: Reply ignores important context
- too_generic: Reply is too generic and not personalized
- unhelpful: Reply does not help the customer
- incomplete: Reply misses important parts of the request
- historical_customer_info: Reply assumes historical info is current
- unsupported_timeline: Reply makes timeline claims without evidence
- unsupported_price: Reply makes price claims without evidence
- unsupported_policy: Reply cites policies without evidence
- awkward_style: Reply has awkward phrasing or tone
- too_verbose: Reply is unnecessarily long
- too_short: Reply is too brief to be helpful
- retrieval_error: Evidence retrieval appears to have failed
- insufficient_evidence: Available evidence is insufficient
- other: Other issue not covered above

OUTPUT FORMAT:
Return ONLY a JSON object with this exact structure:
{
  "relevance": <1-5>,
  "groundedness": <1-5>,
  "correctness": <1-5>,
  "helpfulness": <1-5>,
  "completeness": <1-5>,
  "style": <1-5>,
  "failure_tags": [<list of tags>],
  "short_rationale": "<brief evidence-based justification, max 100 words>"
}

Do NOT include any other text. Only the JSON object."""


def build_judge_prompt(judge_input: JudgeInput) -> str:
    """Build the complete judge prompt from input.

    Args:
        judge_input: The structured input for the judge.

    Returns:
        The complete prompt string ready for the LLM.
    """
    # Format evidence for the prompt
    evidence_text = "No evidence provided."
    if judge_input.evidence:
        evidence_parts = []
        for i, ev in enumerate(judge_input.evidence[:3], 1):  # Limit to top 3
            evidence_parts.append(f"Evidence {i}: {ev.get('text', str(ev))}")
        evidence_text = "\n".join(evidence_parts)

    # Build the user message
    user_message = f"""Please evaluate the following customer-support reply:

CUSTOMER MESSAGE:
{judge_input.customer_message}

CONVERSATION CONTEXT:
{judge_input.conversation_context or 'No additional context provided.'}

INTENT:
{judge_input.intent or 'Not specified'} (confidence: {judge_input.intent_confidence or 'N/A'})

EVIDENCE:
{evidence_text}

CANDIDATE REPLY:
{judge_input.candidate_reply}

Provide your evaluation as a JSON object with scores for each dimension and any applicable failure tags."""

    return user_message


def build_judge_messages(judge_input: JudgeInput) -> list[dict[str, str]]:
    """Build the messages array for chat-based LLM APIs.

    Args:
        judge_input: The structured input for the judge.

    Returns:
        List of message dictionaries with 'role' and 'content'.
    """
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": build_judge_prompt(judge_input)},
    ]


# Prohibited terms that should NOT appear in judge input
PROHIBITED_TERMS = [
    "system_name",
    "model_name",
    "provider",
    "human_score",
    "expected_score",
    "ground_truth",
    "gold_label",
    "baseline",
    "final_system",
    "openai",
    "anthropic",
    "google",
    "gpt-",
    "claude",
    "gemini",
]


def validate_prompt_safety(prompt: str) -> tuple[bool, list[str]]:
    """Check that prompt does not contain prohibited metadata.

    Args:
        prompt: The prompt to validate.

    Returns:
        Tuple of (is_safe, list_of_violations).
    """
    violations = []
    prompt_lower = prompt.lower()

    for term in PROHIBITED_TERMS:
        if term.lower() in prompt_lower:
            violations.append(f"Prohibited term found: {term}")

    return len(violations) == 0, violations