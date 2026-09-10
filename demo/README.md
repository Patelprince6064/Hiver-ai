# AI Support Agent — Interactive CLI Demo

This directory documents the interactive command-line demonstration for the Hiver AI Customer Support Agent.

---

## Requirements

- Python 3.10+
- Installed dependencies: `pip install -r requirements.txt`
- No external GPU or cloud API keys required for mock demonstration mode.

---

## Setup

Activate your project virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

---

## Mock Mode

By default, the demo runs in **Mock Mode** using intelligent deterministic components that replicate real classifier confidence distributions, retrieval passages, and escalation rules.

- **Zero Cloud API Dependencies:** Runs locally in sub-second time.
- **Reproducible Decisions:** Guarantees consistent demonstration of routing behaviors.

---

## Real LLM Mode (Optional)

To run the agent against live OpenAI models:

1. Copy `.env.example` to `.env`.
2. Add your API key: `OPENAI_API_KEY=sk-...`.
3. Pass the `--live` flag to the script:
   ```bash
   python scripts/run_agent.py --message "Where is my package?" --live --demo
   ```

---

## Run Demo

### 1. Run Complete 3-Scenario Demonstration Suite
Executes routine auto-handle, low-confidence escalation, and safety-critical escalation scenarios:

```bash
python scripts/run_agent.py --demo
```

### 2. Run Interactive Single Message Demo
Process any arbitrary customer message through the agent:

```bash
python scripts/run_agent.py --message "Where is my order #12345?" --demo
```

```bash
python scripts/run_agent.py --message "Cancel my account and issue a refund immediately" --demo
```

---

## Example Input

```
Where is my order #12345? Tracking shows it shipped 2 days ago.
```

---

## Expected Output Structure

The demo prints structured decision metadata without exposing raw hidden chain-of-thought:

```text
==================================================
AI SUPPORT AGENT DEMO
==================================================
Customer:
Where is my order #12345? Tracking shows it shipped 2 days ago.

Intent:
order_status

Intent Confidence:
0.860

Retrieved Evidence:
Historical support passage: Orders ship within 1-2 business days and tracking details update via email.

Evidence Status:
SUFFICIENT

Draft Reply:
Your order has shipped and tracking information typically updates within 24 to 48 hours.

Grounding:
PASS

Final Decision:
AUTO_HANDLE

Reason:
Confidence and verification thresholds satisfied for safe auto-handling.
==================================================
```

---

## Troubleshooting

- **ModuleNotFoundError: No module named 'src'**:
  Ensure you are running the command from the repository root: `cd hiver-ai-support-agent`.
- **UnicodeDecodeError on Windows**:
  The CLI demo uses strict ASCII box-formatting compatible with standard Windows PowerShell (cp1252) and Unix terminals.

---

## Safety Behavior: Fail-Closed Principle

Whenever the agent encounters:
1. Low intent confidence (< 0.70)
2. Insufficient or empty historical retrieval evidence
3. Unverified or hallucinated draft claims
4. High-risk actions (account deletion, refund disputes, legal threats)

The decision defaults immediately to **`ESCALATE_TO_HUMAN`**, attaching structured metadata and escalation reason codes for human specialists.
