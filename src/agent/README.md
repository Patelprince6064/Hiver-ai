# Source — Agent

Full agent orchestration: ties together preprocessing, intent, retrieval, generation, and escalation.

## Status: COMPLETE (Phase 17)

## Architecture

```
Customer Message
       |
       v
Input Validation
       |
       v
Intent Classification (Phase 8)
       |
       v
Semantic Retrieval (Phase 10)
       |
       v
Evidence Selection (Phase 12)
       |
       v
Grounded Reply Generation (Phase 12)
       |
       v
Grounding Verification (Phase 13)
       |
       v
Escalation Decision (Phase 15-16)
       |
       +--------------------+
       |                    |
       v                    v
AUTO_HANDLE          ESCALATE_TO_HUMAN
```

## Modules

- `agent_schema.py` - Request/response schemas
- `input_validation.py` - Input validation
- `trace.py` - Structured execution trace
- `support_agent.py` - Main orchestrator

## Usage

```python
from src.agent.support_agent import create_agent
from src.agent.agent_schema import AgentRequest

agent = create_agent(mock_mode=True)
request = AgentRequest(message="Where is my order?")
response = agent.process(request)

if response.decision == "AUTO_HANDLE":
    print(response.reply)
else:
    print(response.human_review)
```

## Safety

- Fail-closed: any critical failure -> ESCALATE_TO_HUMAN
- No external actions (refunds, account changes)
- Grounding verification mandatory
- Mock mode for testing without API keys
