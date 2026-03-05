# Compliance Validation Results

Generated: 2025-08-29 19:08:37
Total Cases: 5

## Validation Summary

| Case ID   | Timestamp                  | Legal-BERT Decision (Conf.)   | Rules-Based Decision (Conf.)   | LLM+RAG Decision (Conf.)   | Final Ensemble Decision   |   Ensemble Confidence | Auto-Approved   | Agreement Level   | Flags   | Notes                                     |
|:----------|:---------------------------|:------------------------------|:-------------------------------|:---------------------------|:--------------------------|----------------------:|:----------------|:------------------|:--------|:------------------------------------------|
| CASE-001  | 2025-08-29T19:08:37.103046 | Non-Compliant (0.43)          | Compliant (0.95)               | Compliant (0.70)           | Compliant                 |                  0.82 | No              | Majority          | None    | Majority vote: Compliant (2/3 models)     |
| CASE-002  | 2025-08-29T19:08:37.143659 | Non-Compliant (0.49)          | Non-Compliant (0.80)           | Unclear (0.60)             | Non-Compliant             |                  0.65 | No              | Majority          | None    | Majority vote: Non-Compliant (2/3 models) |
| CASE-003  | 2025-08-29T19:08:37.192268 | Non-Compliant (0.45)          | Compliant (0.95)               | Compliant (0.70)           | Compliant                 |                  0.82 | No              | Majority          | None    | Majority vote: Compliant (2/3 models)     |
| CASE-004  | 2025-08-29T19:08:37.230889 | Non-Compliant (0.41)          | Compliant (0.99)               | Compliant (0.70)           | Compliant                 |                  0.84 | No              | Majority          | None    | Majority vote: Compliant (2/3 models)     |
| CASE-005  | 2025-08-29T19:08:37.270972 | Non-Compliant (0.44)          | Unclear (0.50)                 | Unclear (0.60)             | Unclear                   |                  0.55 | No              | Majority          | None    | Majority vote: Unclear (2/3 models)       |

## Detailed Results

### Case CASE-001

**Text:** The organization maintains full compliance with all applicable data protection regulations and regularly conducts compliance audits to ensure ongoing adherence to legal requirements.

**Timestamp:** 2025-08-29T19:08:37.103046

**Final Decision:** Compliant (Confidence: 0.82)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.43)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.95)
  - Reasoning: Applied 1 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-002

**Text:** The company violated multiple safety regulations and failed to implement required safety protocols, resulting in significant penalties and enforcement actions.

**Timestamp:** 2025-08-29T19:08:37.143659

**Final Decision:** Non-Compliant (Confidence: 0.65)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.49)
  - Reasoning: No reasoning method available
- **Rules-Based:** Non-Compliant (Confidence: 0.80)
  - Reasoning: Applied 1 rules and keyword scoring
- **LLM+RAG:** Unclear (Confidence: 0.60)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Non-Compliant (2/3 models)

---

### Case CASE-003

**Text:** The project requires further assessment to determine compliance status with environmental regulations. Additional review may be necessary.

**Timestamp:** 2025-08-29T19:08:37.192268

**Final Decision:** Compliant (Confidence: 0.82)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.45)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.95)
  - Reasoning: Applied 2 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-004

**Text:** Our financial reporting procedures are certified compliant with SEC requirements and we maintain all necessary documentation for regulatory review.

**Timestamp:** 2025-08-29T19:08:37.230889

**Final Decision:** Compliant (Confidence: 0.84)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.41)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.99)
  - Reasoning: Applied 3 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-005

**Text:** The data processing activities may or may not comply with GDPR requirements depending on the specific use case and data subject consent.

**Timestamp:** 2025-08-29T19:08:37.270972

**Final Decision:** Unclear (Confidence: 0.55)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.44)
  - Reasoning: No reasoning method available
- **Rules-Based:** Unclear (Confidence: 0.50)
  - Reasoning: Applied 0 rules and keyword scoring
- **LLM+RAG:** Unclear (Confidence: 0.60)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Unclear (2/3 models)

---

