---
name: empirical-paper-review
description: Audit and review Original Research / Empirical Papers and their accompanying experimental codebases against strict IMRaD, statistical rigor, reproducibility, data-to-figure consistency, and anti-leakage standards.
---

# Empirical Research & Experimental Codebase Review Protocol

## Core Objective
Evaluate whether an empirical study and its experimental codebase genuinely generate novel, reproducible knowledge by testing a strictly falsifiable hypothesis through primary empirical data, observation, or simulation. Cross-verify textual claims in the manuscript against actual implementation details, data splits, evaluation scripts, and generated figures.

---

## Step 1: Audit Execution Workflow
When invoked on a paper (PDF/text), a code repository, or both, execute the review in this exact order:

1. **Extract Core Claims & Hypothesis:** Identify the primary research question, explicit hypotheses, claimed breakthroughs, and key numerical results from the Abstract, Introduction, and Conclusion.
2. **Trace Claims to Evidence (IMRaD Mapping):** Map every headline claim in the Introduction directly to its corresponding table, figure, or statistical test in the Results section—and, where code is available, to the exact script and configuration file that produced it.
3. **Evaluate Against the 7-Pillar Rubric:** Score and critique each dimension below using concrete citations (page/section numbers, table/figure IDs, or `file:line` code references).
4. **Screen for Critical Red Flags:** Explicitly check for fatal methodological or implementation flaws that invalidate the findings.
5. **Deliver Structured Verdict:** Output the standardized review report defined in Step 4.

---

## Step 2: 7-Pillar Evaluation Rubric

### 1. Problem Formulation & Hypothesis Construction
* **Paper Audit:** Verify that the research question is specific, strictly falsifiable, and anchored in a verified gap in existing literature (not a strawman problem).
* **Code Audit:** Confirm that loss functions, reward signals, or evaluation objectives in the codebase directly operationalize the stated hypothesis rather than optimizing a proxy metric disconnected from the research question.

### 2. Structural Logic (IMRaD Rigor) & "Bait-and-Switch" Check
* **Paper Audit:** Enforce strict 1-to-1 fidelity between claims in the Abstract/Introduction and empirical evidence in the Results. Flag any **bait-and-switch fallacy** (e.g., motivating the paper with a complex, noisy real-world problem, then benchmarking exclusively on a toy or oversimplified synthetic dataset).
* **Code Audit:** Inspect dataset loaders and preprocessing scripts (`data/`, `datasets/`, `preprocess.py`) to verify that real-world complexity is preserved and not stripped away via undocumented filtering, cherry-picked subsets, or unrealistic assumptions.

### 3. Methodology, Controls & Statistical Rigor
* **Variable Isolation:** Confirm independent, dependent, and confounding variables are cleanly isolated. Check config files to ensure only the target variable changes across comparative runs.
* **Fair Baseline Tuning:** Verify that competitive baselines receive equivalent hyperparameter tuning budgets, compute bounds, and search grids. Flag hardcoded or default hyperparameters for baselines alongside heavily tuned grids for the proposed method.
* **Ablations & Statistical Power:**
  * Check for systematic ablation studies isolating each proposed component.
  * Verify whether sample sizes / power calculations are justified.
  * Check evaluation scripts for **multiple distinct random seeds** (not a single cherry-picked seed) and verify formal hypothesis testing reporting **effect sizes** and **confidence intervals (CIs)** alongside $p$-values.

### 4. Data-to-Figure & Code-to-Plot Consistency
* **Numerical Fidelity:** Cross-check exact numbers mentioned in prose against summary tables, raw logs, and plotted coordinates.
* **Dispersion Metrics:** Verify that plots and tables report appropriate variance/dispersion metrics (error bars, standard deviation, IQR, or shaded confidence bands)—never bare point estimates alone.
* **Visual Integrity:** Check plotting scripts (`matplotlib`, `seaborn`, `pgfplots`) and rendered figures for deceptively truncated axes, inconsistent scales across subplots, or selectively cropped qualitative examples designed to exaggerate marginal gains.

### 5. Citation Integrity & Originality
* **Paper Audit:** Assess whether Related Work provides an independent, critical synthesis rather than superficial summary or copy-pasted phrasing. Check for explicit disclosure of prior workshop/preprint versions and inspect qualitative figures for duplicated or selectively altered sub-images.
* **Code Audit:** Check third-party attributions, license headers, and vendored forks to ensure baseline implementations are faithfully credited and unmodified in ways that degrade their performance.

### 6. Limitations & Failure Modes
* **Paper Audit:** Reject superficial, boilerplate limitations (e.g., *"future work will explore larger datasets"*). Require concrete analysis of underperforming subgroups, confusion matrix failure modes, edge cases, and operational boundaries where the method breaks down.
* **Code Audit:** Check error analysis scripts and slice-based evaluation logic to verify whether failure cases were systematically probed or ignored.

### 7. Scalability & Complexity
* **Paper Audit:** Verify formal time/space complexity analysis ($\mathcal{O}$-notation) alongside empirical scaling benchmarks as input size, dimensionality, or agent/model scale increases.
* **Code Audit:** Inspect model architectures, inner loops, memory allocations, and profiling scripts for hidden quadratic bottlenecks, unbatched operations, or wall-clock/memory overhead omitted from main comparison tables.

---

## Step 3: Critical Red Flags (Automatic Escalation)
Immediately flag and escalate any occurrence of the following fatal flaws:

* **[RED FLAG 1] Weakened / Outdated Baselines:** Comparing the proposed method solely against obsolete models, un-tuned defaults, or crippled baseline configurations.
* **[RED FLAG 2] Train-Test Contamination / Data Leakage:** Fitting scalers, tokenizers, feature selectors, or imputation statistics before splitting data; overlapping entities/timestamps across train/val/test splits; or tuning hyperparameters directly on the test set.
* **[RED FLAG 3] Numerical & Visual Mismatch:** Discrepancies between numbers reported in text, summary tables, plotted figures, and raw experiment logs.
* **[RED FLAG 4] Suppressed Variance & Negative Results:** Hiding run-to-run variance, omitting failed seeds/runs, or dropping datasets/metrics where the proposed method underperforms.

---

## Step 4: Required Output Format

Keep the review **concise, scannable, and high-signal** (target ~250–400 words):
* **No filler or generic praise:** Skip summarizing the paper's background; go straight to verdict, evidence, and flaws.
* **Cite inline:** Use compact citations (`p.X`, `Table Y`, `Fig. Z`, `file:line`) instead of prose explanations.
* **Prioritize impact:** Highlight only the top 2–4 core claims (especially mismatches/unverified ones) and top 3–5 actionable fixes.

Structure every review strictly using the template below:

```markdown
# Review Report: [Paper/Repo Title]

## 1. Verdict & Red Flags
* **Decision:** [Accept / Minor Revision / Major Revision / Reject]
* **Core Takeaway:** [1 sentence: does the evidence/code actually support the main hypothesis?]
* **Red Flags:** [None OR bulleted list of triggered Red Flags with exact `p.X`/`Table Y`/`file:line` evidence]

## 2. Core Claim-to-Evidence Check (Top 2–4 Claims)
| Core Claim (`Sec/p.`) | Evidence (`Table/Fig` or `file:line`) | Status |
| :--- | :--- | :--- |
| ... | ... | Verified / Mismatch / Unverified |

## 3. Pillar Scores (1 line per pillar)
| Pillar | Score | Key Finding (concise, evidence-backed) |
| :--- | :--- | :--- |
| 1. Problem & Hypothesis | X/5 | ... |
| 2. IMRaD & Bait-and-Switch | X/5 | ... |
| 3. Controls & Statistics | X/5 | ... |
| 4. Data-to-Figure Fidelity | X/5 | ... |
| 5. Citations & Originality | X/5 | ... |
| 6. Limitations & Failure Modes | X/5 | ... |
| 7. Scalability & Complexity | X/5 | ... |

## 4. Top Action Items (Max 5, Prioritized)
1. **[Blocking]:** ...
2. **[Stats / Method]:** ...
3. **[Code / Reproducibility]:** ...
```