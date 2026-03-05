# Compliance Validation Results

Generated: 2025-08-29 17:56:44
Total Cases: 5

## Validation Summary

| Case ID   | Timestamp                  | Legal-BERT Decision (Conf.)   | Rules-Based Decision (Conf.)   | LLM+RAG Decision (Conf.)   | Final Ensemble Decision   |   Ensemble Confidence | Auto-Approved   | Agreement Level   | Flags   | Notes                                 |
|:----------|:---------------------------|:------------------------------|:-------------------------------|:---------------------------|:--------------------------|----------------------:|:----------------|:------------------|:--------|:--------------------------------------|
| CASE-001  | 2025-08-29T17:56:44.097505 | Non-Compliant (0.46)          | Compliant (0.95)               | Compliant (0.70)           | Compliant                 |                  0.82 | No              | Majority          | None    | Majority vote: Compliant (2/3 models) |
| CASE-002  | 2025-08-29T17:56:44.152039 | Unclear (0.39)                | Non-Compliant (0.80)           | Unclear (0.60)             | Unclear                   |                  0.49 | No              | Majority          | None    | Majority vote: Unclear (2/3 models)   |
| CASE-003  | 2025-08-29T17:56:44.218323 | Non-Compliant (0.47)          | Compliant (0.95)               | Compliant (0.70)           | Compliant                 |                  0.82 | No              | Majority          | None    | Majority vote: Compliant (2/3 models) |
| CASE-004  | 2025-08-29T17:56:44.286097 | Unclear (0.40)                | Compliant (0.99)               | Compliant (0.70)           | Compliant                 |                  0.84 | No              | Majority          | None    | Majority vote: Compliant (2/3 models) |
| CASE-005  | 2025-08-29T17:56:44.399915 | Non-Compliant (0.44)          | Unclear (0.50)                 | Unclear (0.60)             | Unclear                   |                  0.55 | No              | Majority          | None    | Majority vote: Unclear (2/3 models)   |

## Detailed Results

### Case CASE-001

**Text:** The organization maintains full compliance with all applicable data protection regulations and regularly conducts compliance audits to ensure ongoing adherence to legal requirements.

**Timestamp:** 2025-08-29T17:56:44.097505

**Final Decision:** Compliant (Confidence: 0.82)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.46)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.95)
  - Reasoning: Applied 1 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-002

**Text:** The company violated multiple safety regulations and failed to implement required safety protocols, resulting in significant penalties and enforcement actions.

**Timestamp:** 2025-08-29T17:56:44.152039

**Final Decision:** Unclear (Confidence: 0.49)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Unclear (Confidence: 0.39)
  - Reasoning: No reasoning method available
- **Rules-Based:** Non-Compliant (Confidence: 0.80)
  - Reasoning: Applied 1 rules and keyword scoring
- **LLM+RAG:** Unclear (Confidence: 0.60)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Unclear (2/3 models)

---

### Case CASE-003

**Text:** The project requires further assessment to determine compliance status with environmental regulations. Additional review may be necessary.

**Timestamp:** 2025-08-29T17:56:44.218323

**Final Decision:** Compliant (Confidence: 0.82)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Non-Compliant (Confidence: 0.47)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.95)
  - Reasoning: Applied 2 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-004

**Text:** Our financial reporting procedures are certified compliant with SEC requirements and we maintain all necessary documentation for regulatory review.

**Timestamp:** 2025-08-29T17:56:44.286097

**Final Decision:** Compliant (Confidence: 0.84)

**Auto-Approved:** No

**Model Predictions:**

- **Legal-BERT:** Unclear (Confidence: 0.40)
  - Reasoning: No reasoning method available
- **Rules-Based:** Compliant (Confidence: 0.99)
  - Reasoning: Applied 3 rules and keyword scoring
- **LLM+RAG:** Compliant (Confidence: 0.70)
  - Reasoning: Retrieved 3 relevant regulatory contexts

**Notes:** Majority vote: Compliant (2/3 models)

---

### Case CASE-005

**Text:** The data processing activities may or may not comply with GDPR requirements depending on the specific use case and data subject consent.

**Timestamp:** 2025-08-29T17:56:44.399915

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

