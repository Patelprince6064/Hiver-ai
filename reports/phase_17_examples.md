# Phase 17 — End-to-End Examples

## AUTO_HANDLE Examples

### Example 1: Order Status Inquiry

**INPUT:**
```
"Where is my order? I placed it 3 days ago."
```

**INTENT:** order_status
**CONFIDENCE:** 0.85
**RETRIEVED EVIDENCE:**
- KB001: "Your order is on the way and should arrive in 2-3 business days."
- KB002: "You can track your order using the tracking link in your email."
- KB003: "Standard shipping typically takes 3-5 business days."

**GROUNDING STATUS:** pass
**ESCALATION SIGNALS:** None
**FINAL DECISION:** AUTO_HANDLE
**REPLY:**
```
Your order is on the way and should arrive soon. You can track it using
the tracking link sent to your email. Standard shipping typically takes
3-5 business days.
```

---

### Example 2: Return Policy Question

**INPUT:**
```
"What is your return policy?"
```

**INTENT:** return
**CONFIDENCE:** 0.82
**RETRIEVED EVIDENCE:**
- KB001: "You can return items within 30 days of purchase."
- KB002: "Items must be unused and in original packaging."
- KB003: "Return shipping is free for defective items."

**GROUNDING STATUS:** pass
**ESCALATION SIGNALS:** None
**FINAL DECISION:** AUTO_HANDLE
**REPLY:**
```
You can return items within 30 days of purchase. Items must be unused
and in original packaging. Return shipping is free for defective items.
```

---

### Example 3: Password Reset

**INPUT:**
```
"How do I reset my password?"
```

**INTENT:** account_management
**CONFIDENCE:** 0.88
**RETRIEVED EVIDENCE:**
- KB001: "You can reset your password from the login page."
- KB002: "Click 'Forgot Password' and follow the email instructions."
- KB003: "If you don't receive the email, check your spam folder."

**GROUNDING STATUS:** pass
**ESCALATION SIGNALS:** None
**FINAL DECISION:** AUTO_HANDLE
**REPLY:**
```
You can reset your password from the login page. Click "Forgot Password"
and follow the instructions sent to your email. If you don't receive the
email, check your spam folder.
```

---

## ESCALATE_TO_HUMAN Examples

### Example 4: Low Intent Confidence

**INPUT:**
```
"asdfghjkl qwerty"
```

**INTENT:** unknown
**CONFIDENCE:** 0.30
**RETRIEVED EVIDENCE:** None
**GROUNDING STATUS:** N/A
**ESCALATION SIGNALS:**
- LOW_INTENT_CONFIDENCE

**FINAL DECISION:** ESCALATE_TO_HUMAN
**HUMAN REVIEW PACKAGE:**
```
Customer Message: "asdfghjkl qwerty"
Predicted Intent: unknown (confidence: 0.30)
Escalation Reasons: LOW_INTENT_CONFIDENCE
Recommended Action: Review conversation and respond manually.
```

---

### Example 5: Insufficient Evidence

**INPUT:**
```
"What is your policy on quantum computing returns?"
```

**INTENT:** return
**CONFIDENCE:** 0.75
**RETRIEVED EVIDENCE:** No relevant matches
**GROUNDING STATUS:** insufficient_evidence
**ESCALATION SIGNALS:**
- INSUFFICIENT_EVIDENCE

**FINAL DECISION:** ESCALATE_TO_HUMAN
**HUMAN REVIEW PACKAGE:**
```
Customer Message: "What is your policy on quantum computing returns?"
Predicted Intent: return (confidence: 0.75)
Escalation Reasons: INSUFFICIENT_EVIDENCE
Recommended Action: No sufficient historical evidence available.
```

---

### Example 6: Account-Specific Action

**INPUT:**
```
"I want to delete my account"
```

**INTENT:** account_action
**CONFIDENCE:** 0.85
**RETRIEVED EVIDENCE:**
- KB001: "Please contact support for account changes."

**GROUNDING STATUS:** pass
**ESCALATION SIGNALS:**
- ACCOUNT_ACTION_REQUIRED

**FINAL DECISION:** ESCALATE_TO_HUMAN
**HUMAN REVIEW PACKAGE:**
```
Customer Message: "I want to delete my account"
Predicted Intent: account_action (confidence: 0.85)
Escalation Reasons: ACCOUNT_ACTION_REQUIRED
Recommended Action: Account deletion requires human verification.
Draft Reply (UNSENT): "I can help you delete your account. Please confirm."
```

---

## Failure Examples

### Example 7: Intent Classifier Failure

**INPUT:**
```
"Can I get a price match on my order?"
```

**COMPONENT FAILURE:** Intent classifier threw exception
**ERROR:** Classifier model failed to load
**FINAL DECISION:** ESCALATE_TO_HUMAN
**REASON:** Provider error (system failure)

---

### Example 8: Retrieval System Failure

**INPUT:**
```
"I need help with my recent order."
```

**COMPONENT FAILURE:** Retrieval index not available
**ERROR:** FAISS index not loaded
**FINAL DECISION:** ESCALATE_TO_HUMAN
**REASON:** Retrieval failure (system failure)
