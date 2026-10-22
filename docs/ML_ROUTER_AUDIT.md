# ML Router Verification & Empirical Audit Report
**Project:** Autonomous AI Multi-Agent Orchestration Platform  
**Auditor:** Automated Empirical Audit Suite  
**Date:** October 2026  
**Artifact:** `docs/ML_ROUTER_AUDIT.md`  

---

## 1. Executive Summary
This audit empirically verifies the machine learning task router responsible for assigning tasks across local on-premise models and cloud fallbacks.
- **Deduplication & Leakage Status:** PASSED (0.00% leakage across partitions)
- **Held-Out Test Set Size:** 148 samples (25% held-out test split)
- **Mean 5-Fold Stratified CV Accuracy:** 99.66% (+/- 0.42%)
- **Test Set Accuracy:** 99.32%
- **Test Set Macro F1:** 99.13%
- **Local Execution Ratio:** 87.8% on-premises

---

## 2. Comparative Baseline Analysis

| Strategy / Method | Accuracy | Macro F1 | Absolute Gain vs Random | Relative Gain vs Heuristic |
| :--- | :---: | :---: | :---: | :---: |
| **Random Baseline** | 22.30% | 19.39% | Baseline | - |
| **Majority Class (DeepSeek Coder)** | 43.92% | 15.26% | +21.62% | - |
| **Rule Heuristics** | 93.24% | 89.29% | +70.95% | Baseline |
| **Trained ML Router (Random Forest)** | **99.32%** | **99.13%** | **+77.03%** | **+6.08%** |

---

## 3. Per-Class Metrics Breakdown (Held-Out Test Set N=148)

| Target Model | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Qwen 2.5 (General)** | 100.00% | 100.00% | 100.00% | 50 |
| **DeepSeek Coder (Code)** | 98.48% | 100.00% | 99.24% | 65 |
| **Llama 3.2 (Summarization)** | 100.00% | 100.00% | 100.00% | 14 |
| **Gemini 3.5 (Cloud Fallback)** | 100.00% | 94.74% | 97.30% | 19 |

---

## 4. Confusion Matrix

| Actual \ Predicted | Qwen 2.5 | DeepSeek Coder | Llama 3.2 | Gemini 3.5 |
| :--- | :---: | :---: | :---: | :---: |
| **Qwen 2.5** | 50 | 0 | 0 | 0 |
| **DeepSeek Coder** | 0 | 65 | 0 | 0 |
| **Llama 3.2** | 0 | 0 | 14 | 0 |
| **Gemini 3.5** | 0 | 1 | 0 | 18 |


---

## 5. Speed, Latency & Stated Pricing Assumptions

### Stated Pricing Assumptions:
- **Commercial Cloud (Gemini 3.5 Flash):** $0.10 / 1M prompt tokens ($0.00010/1k), $0.40 / 1M completion tokens ($0.00040/1k). Standard prompt/completion ratio yields **~$0.000150 per task**.
- **On-Premise Local Ollama:** **$0.000000 marginal token cost** (workstation compute).

### Comparative Operational Telemetry:
| Strategy | Avg Latency | Total Cost (Test Set N=148) | Local Execution % | Privacy & Sovereignty |
| :--- | :---: | :---: | :---: | :---: |
| **All-Cloud Strategy (Gemini 3.5)** | 450.0 ms | $0.02220 | 0.0% | Egress on 100% of tasks |
| **All-Local Strategy (Ollama Qwen)** | 850.0 ms | $0.00000 | 100.0% | 100% on-premises |
| **ML Router Hybrid Strategy** | **827.0 ms** | **$0.00270** | **87.8%** | **Strict data sovereignty enforced** |

---

## 6. Evaluation Limitations
1. **Synthetic Task Distribution:** Features are bootstrapped from parameterized historical distributions representing real software development tasks.
2. **Metadata Dependency:** Router performance assumes the Master Planner accurately tags complexity and keyword features.
3. **Hardware Heterogeneity:** Steady-state latency reflects loaded model memory; cold starts on consumer GPUs will exhibit an initial delay.
