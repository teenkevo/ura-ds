This is the WHT exemption model

# Withholding Tax Exemption AI Model  
Uganda Revenue Authority – End-to-End Design & Documentation

---

## 1. Legal and policy context

This design is for a withholding tax (WHT) exemption decision-support system for Uganda Revenue Authority (URA). It aligns with:

- The Income Tax Act (including provisions that govern WHT and exemptions {119, 122, 123, 124, 125, 126, 127, 128 }).  
- URA’s public WHT exemption notice and checklist for FY 2023/24, which:  
  - Defines eligibility conditions for exemption.  
  - Sets a fixed exemption period (typically 12 months, e.g. 1 July – 30 June).  
  - Clarifies that exemption can be revoked if the taxpayer becomes non-compliant during the exemption period.  

The AI model does **not** replace the law or the checklist. It automates and standardises:

1. Evaluating the full WHT exemption checklist for each applicant.  
2. Assessing additional risk and behaviour signals from URA data.  
3. Prioritising and partially automating decisions, while preserving human oversight.

Legal roles:

- **Law and policy** define which conditions are mandatory, optional, or risk indicators.  
- **The model** turns these conditions into measurable features and risk scores.  
- **Officers** remain responsible for final decisions and overrides.

---

## 2. Decision architecture

### 2.1 Objectives

The system is designed to:

1. Apply the WHT exemption checklist consistently and quickly.  
2. Identify low-risk, high-compliance taxpayers suitable for automatic or fast-tracked exemption.  
3. Flag borderline or risky cases for human review.  
4. Support revocation decisions if behaviour deteriorates during the exemption period.  
5. Provide auditable, explainable decisions.

### 2.2 Where the WHT exemption AI sits

```text
[TAXPAYER]
   │
   ▼
Online WHT Exemption Application
(e-Services → e-Registration → WHT Exemption)
   │
   ▼
AI-Assisted Decision Engine
   │         │
   │         ├─ Rule Layer (hard legal & policy rules)
   │         │
   │         └─ ML Risk Layer (probability of “safe to exempt”)
   │
   ▼
Decision + Reasons
(Approve / Reject / Route to Officer)
   │
   ▼
Monitoring & Revocation Logic
(Continuous compliance checks during exemption year)
```

Key principles:

- All decisions are grounded in explicit legal rules and checklist questions.  
- The machine-learning (ML) layer can **inform** but not silently override non-negotiable legal rules.  
- Every decision is explainable: the system can show which rules and features led to the outcome.

---

## 3. Data and feature flow

### 3.1 High-level data pipeline

```text
[Source Systems]
  - TIN registry
  - Tax type registrations
  - Income tax returns
  - VAT returns
  - PAYE returns
  - WHT returns
  - WHT agents registry
  - EFRIS invoices
  - Tax stamps and LED data
  - Assessments & payments ledger
  - Penalties ledger
  - Enforcement actions
  - Waiver applications
  - Investigations
  - Disputes

        │
        ▼
[Data Cleaning & Standardisation]
  - TIN formatting
  - Dates, currencies, tax periods
  - Joining taxpayers and directors

        │
        ▼
[Feature Engineering Layer]
  - Direct checklist-derived features (Q1–Q30)
  - Behavioural metrics (ratios, counts, recency)
  - Composite scores (compliance, transparency, enforcement risk, stability)

        │
        ▼
[Model Layer]
  - Rule engine (hard legal rules)
  - ML model (probability of “safe to exempt”)

        │
        ▼
[Decision Outputs]
  - Approve / Reject / Human review
  - Reasons and evidence
  - Monitoring and revocation triggers
```

---

## 4. Feature engineering from the WHT exemption checklist

Each question on the WHT exemption checklist becomes one or more **features** in the model. This section shows:

- The original checklist question (Q1–Q30).  
- The engineered features.  
- The intuition behind each feature.

> **Note on naming:**  
> In the conceptual list below, features are shown with simple names (e.g. `has_all_director_tins`).  
> In the data dictionary and implementation, these map to names prefixed with `wht_<group>_...` (e.g. `wht_profile_has_all_director_tins`).

---

### 4.1 Registration & profile features (Q1–5)

**Q1. Directors/associates have TINs?**  
- `has_all_director_tins` (boolean)  
- `director_tin_coverage_ratio = directors_with_tin / total_directors`  
- Intuition: if directors lack TINs, transparency and traceability risk increases.

**Q2. Active TIN and ≥3 years on register?**  
- `tin_active` (boolean)  
- `years_on_register` (numeric)  
- `is_mature_taxpayer = years_on_register >= 3`  
- Intuition: new taxpayers may be less predictable; seasoned taxpayers easier to judge and audit.

**Q3. If <3 years, importing plant & machinery CIF ≥ USD 150,000?**  
- `is_new_taxpayer` (boolean)  
- `plant_machinery_import_value_usd` (numeric)  
- `meets_investment_threshold` (boolean)  
- Intuition: new but high-investment taxpayers might deserve different risk treatment than small, low-investment entities.

**Q4. Existing Income Tax exemption?**  
- `has_other_income_tax_exemption` (boolean)  
- Intuition: checks for double benefits and special regimes; may require extra scrutiny or a different process.

**Q5. Registration profile up to date (address, tax types, directors, info)?**  
- `profile_last_update_date` (date)  
- `profile_update_recency_days` (numeric)  
- `profile_is_complete` (boolean)  
- Intuition: updated, complete profiles indicate more engaged, lower-risk taxpayers.

---

### 4.2 VAT / EFRIS / Tax stamps / Tax agent (Q6–8)

**Q6. Issuing EFRIS invoices/receipts to all clients (if VAT-registered)?**  
- `is_vat_registered` (boolean)  
- `efris_usage_ratio = efris_invoices_amount / total_declared_sales_amount`  
- `efris_fully_compliant` (boolean; e.g. `efris_usage_ratio >= 0.95`)  
- Intuition: EFRIS shows transaction-level visibility; low usage suggests under-reporting or informality.

**Q7. Applying tax stamps to all applicable products (for LED taxpayers)?**  
- `is_led_registered` (boolean)  
- `tax_stamp_coverage_ratio = stamped_units / stampable_units`  
- `tax_stamp_noncompliance_incidents` (count over a defined period)  
- Intuition: low coverage or past stamp violations suggest smuggling or under-declaration risk.

**Q8. Have a tax agent (Tax Procedures Code) – and does the agent have a TIN?**  
- `has_tax_agent` (boolean)  
- `tax_agent_tin_valid` (boolean)  
- `tax_agent_risk_score` (optional numeric, if URA scores agents)  
- Intuition: compliant, reputable agents correlate with better compliance; risky agents may correlate with problematic behaviour.

---

### 4.3 WHT agent behaviour (Q9–12)

**Q9. Registered for WHT as a tax type?**  
- `is_wht_registered` (boolean)  
- Intuition: WHT exemption is more meaningful if WHT is a relevant tax for the entity.

**Q10. Designated WHT agent?**  
- `is_designated_wht_agent` (boolean)  
- Intuition: designated agents hold more responsibility; failure here is more serious.

**Q11. Deducting & remitting WHT in time?**  
- `wht_returns_expected_12m` (count)  
- `wht_returns_filed_12m` (count)  
- `wht_filing_compliance_ratio = wht_returns_filed_12m / wht_returns_expected_12m`  
- `wht_avg_payment_delay_days` (average days between due date and actual payment)  
- Intuition: WHT filing and payment compliance is a core indicator of reliability.

**Q12. Declaring all local suppliers’ TINs in WHT returns?**  
- `supplier_tin_coverage_ratio = suppliers_with_valid_tins / total_suppliers`  
- `missing_supplier_tins_count` (count of suppliers without valid TINs)  
- Intuition: poor supplier TIN coverage suggests concealment of counterparties or use of informal suppliers.

---

### 4.4 General filing & VAT quality (Q13–15)

**Q13. Filing all returns by due dates?**  
- `overall_filing_compliance_ratio` (across all relevant taxes)  
- `late_returns_last_12m` (count)  
- `max_days_late_return` (numeric)  
- Intuition: timely filing is one of the strongest predictors of general compliance.

**Q14. Apportioning VAT input correctly (for mixed supplies)?**  
- `has_mixed_supplies` (boolean)  
- `vat_apportionment_flag` (boolean; compliant/non-compliant indicator)  
- `vat_input_adjustments_last_12m` (count or amount)  
- Intuition: correct apportionment shows technical compliance; frequent adjustments may signal risky behaviour.

**Q15. Correct customer TINs and names in VAT returns?**  
- `vat_customer_tin_coverage_ratio`  
- `vat_customer_tin_mismatch_count` (TIN/name mismatches)  
- Intuition: errors or deliberate misreporting in customer information weaken audit trails.

---

### 4.5 PAYE & directors’ income (Q16–18)

**Q16. Fully declaring all employees’ remuneration in PAYE returns?**  
- `paye_employee_count_declared`  
- `paye_total_remuneration_declared`  
- `paye_remuneration_to_turnover_ratio`  
- Intuition: mismatches vs expected payroll levels can indicate under-declared salaries or ghost workers.

**Q17. Directors on payroll & declared in PAYE?**  
- `directors_on_payroll_count`  
- `directors_with_paye_tin` (if available)  
- Intuition: excluding directors from payroll can be a way of hiding remuneration.

**Q18. Where directors not on payroll, are they filing individual IT returns & declaring all income?**  
- `directors_filing_personal_returns_ratio`  
- `directors_full_income_declared_flag` (if cross-matching is possible)  
- Intuition: directors’ personal filing behaviour is a strong indicator of corporate culture and risk.

---

### 4.6 Income mix & rental (Q19–21)

**Q19. Declaring rental income separately from business income?**  
- `has_rental_income` (boolean)  
- `has_business_income` (boolean)  
- `rental_separately_declared_flag` (boolean)  
- Intuition: correct separation of rental vs business income prevents base erosion.

**Q20. Expenditure above UGX 5m from suppliers without TIN?**  
- `big_spend_no_tin_count`  
- `big_spend_no_tin_total_amount`  
- Intuition: large spend to suppliers without TINs is a major risk flag for informality or laundering.

**Q21. Providing valid landlord TINs and names in returns?**  
- `landlord_tin_provided_flag`  
- `landlord_tin_valid_flag`  
- Intuition: missing or invalid landlord TINs reduce visibility and can hide related-party arrangements.

---

### 4.7 Profitability, penalties & payments (Q22–25)

**Q22. Making losses in past three financial years?**  
- `years_of_consecutive_loss`  
- `loss_to_turnover_ratio`  
- Intuition: repeated losses can be genuine or a sign of aggressive tax planning; behaviour needs to be contextualised with other features.

**Q23. Penalty for under-estimation of provisional tax in past 5 years?**  
- `underestimation_penalty_flag` (boolean)  
- `underestimation_penalty_count_5y`  
- `underestimation_penalty_amount_5y`  
- Intuition: repeated underestimation suggests systemic understatement of tax due.

**Q24. Paying all taxes by due dates?**  
- `tax_payment_compliance_ratio`  
- `avg_payment_delay_days`  
- `max_payment_delay_days`  
- Intuition: payment behaviour complements filing behaviour; paying late or not at all is a core risk indicator.

**Q25. For small taxpayers: domestic tax payments in last 12 months > UGX 50m?**  
- `is_small_taxpayer` (boolean)  
- `domestic_tax_payments_12m`  
- `meets_minimum_payment_threshold` (boolean)  
- Intuition: for small taxpayers, a minimum payment threshold ensures the exemption targets genuinely active businesses.

---

### 4.8 Outstanding balances & enforcement (Q26–30)

**Q26. Outstanding tax liability – under an approved instalment plan?**  
- `has_outstanding_liability` (boolean)  
- `on_approved_installment_plan` (boolean)  
- `liability_to_turnover_ratio` (numeric)  
- Intuition: managed liabilities under a formal plan are less risky than unmanaged arrears.

**Q27. Enforcement actions (agency notice, distress, customs lien, etc.)?**  
- `enforcement_actions_count_5y`  
- `recent_enforcement_flag` (e.g. within last 12–24 months)  
- Intuition: past enforcement is a strong predictor of future risk.

**Q28. Ledger disputes – engaged URA to resolve?**  
- `disputed_balance_flag`  
- `dispute_resolved_flag`  
- Intuition: disputes themselves are not necessarily bad; engagement and resolution paths are important signals.

**Q29. Applied for or benefitted from a tax waiver?**  
- `tax_waiver_count_5y`  
- `tax_waiver_amount_5y`  
- Intuition: frequent waivers may signal repeated non-compliance or financial stress.

**Q30. Ever investigated by the Tax Investigations Department?**  
- `investigation_flag`  
- `investigation_count`  
- `last_investigation_recency_days`  
- Intuition: prior investigation is a major red flag, especially if recent or repeated.

---

## 5. Composite features: turning many answers into a few powerful signals

Once the base features are computed, they can be combined into a smaller set of composite indicators that are easier to interpret and use. These are policy- and model-driven; exact weights can be tuned empirically and approved by URA.

### 5.1 Overall compliance score

**Name:** `overall_compliance_score` (implemented as `wht_composite_overall_compliance_score`)  
**Range:** 0–100 (higher is better)  

**Inputs (weighted combination):**

- Filing ratios (Q13, Q24)  
  - `overall_filing_compliance_ratio`  
  - `late_returns_last_12m`  
  - `max_days_late_return`  
- WHT behaviour (Q9–12)  
  - `is_wht_registered`  
  - `is_designated_wht_agent`  
  - `wht_filing_compliance_ratio`  
  - `wht_avg_payment_delay_days`  
- PAYE & VAT quality (Q14–16)  
  - `vat_apportionment_flag`  
  - `vat_input_adjustments_last_12m`  
  - `paye_remuneration_to_turnover_ratio`  
  - `paye_employee_count_declared`  

**Normalisation:**  
- Each component is scaled to 0–1.  
- Weighted sum is scaled to 0–100.

**Intuition:**  
Captures how reliably the taxpayer **files and pays** across the main taxes, and how well they comply with WHT and VAT/PAYE technical rules.

---

### 5.2 Enforcement risk score

**Name:** `enforcement_risk_score` (implemented as `wht_composite_enforcement_risk_score`)  
**Range:** 0–100 (higher is more risky)  

**Uses:**

- Q23 – Under-estimation penalties  
  - `underestimation_penalty_flag`  
  - `underestimation_penalty_count_5y`  
  - `underestimation_penalty_amount_5y`  
- Q26 – Liabilities and plans  
  - `has_outstanding_liability`  
  - `on_approved_installment_plan`  
  - `liability_to_turnover_ratio`  
- Q27 – Enforcement actions  
  - `enforcement_actions_count_5y`  
  - `recent_enforcement_flag`  
- Q30 – Investigations  
  - `investigation_flag`  
  - `investigation_count`  
  - `last_investigation_recency_days`  

**Intuition:**  
Higher if there are frequent penalties, large unmanaged liabilities, recent enforcement actions, or investigations. Taxpayers with high enforcement risk scores should rarely be auto-exempted.

---

### 5.3 Transparency score

**Name:** `transparency_score` (implemented as `wht_composite_transparency_score`)  
**Range:** 0–100 (higher is better)  

**Uses:**

- Q1 – Directors’ TINs  
  - `has_all_director_tins`  
  - `director_tin_coverage_ratio`  
- Q5 – Profile completeness  
  - `profile_is_complete`  
- Q12 – Supplier TINs in WHT  
  - `supplier_tin_coverage_ratio`  
  - `missing_supplier_tins_count`  
- Q15 – Customer TINs in VAT  
  - `vat_customer_tin_coverage_ratio`  
  - `vat_customer_tin_mismatch_count`  
- Q18 – Directors’ personal returns  
  - `directors_filing_personal_returns_ratio`  
  - `directors_full_income_declared_flag`  
- Q21 – Landlord TINs  
  - `landlord_tin_provided_flag`  
  - `landlord_tin_valid_flag`  

**Intuition:**  
Measures how much URA can **see** of the taxpayer and its network. Lower scores mean missing or invalid TINs for directors, suppliers, customers, and landlords, or poor director personal filing behaviour.

---

### 5.4 Stability indicator

**Name:** `stability_score` (implemented as `wht_composite_stability_score`)  
**Range:** 0–100 (higher = more stable)  

**Uses:**

- Q2 – Years on register  
  - `years_on_register`  
  - `is_mature_taxpayer`  
- Q19 – Income mix  
  - `has_rental_income`  
  - `has_business_income`  
  - `rental_separately_declared_flag`  
- Q22 – Loss history  
  - `years_of_consecutive_loss`  
  - `loss_to_turnover_ratio`  
- Q24–Q25 – Payment behaviour and volume  
  - `domestic_tax_payments_12m`  
  - `tax_payment_compliance_ratio`  
  - `meets_minimum_payment_threshold`  

**Intuition:**  
Measures whether the taxpayer looks like a **stable, ongoing business** or a short-term vehicle with repeated losses and low genuine activity.

---

### 5.5 Rule violation indicator

**Name:** `any_fatal_legal_failure` (implemented as `wht_rule_any_fatal_legal_failure`)  
**Type:** boolean  

**Uses:**

- Inactive or invalid TIN (Q2).  
- Critical registration failures (profile not valid).  
- Severe enforcement/investigation events if defined as non-negotiable.  
- Any checklist item flagged by URA policy as mandatory, not discretionary.

**Intuition:**  
If this flag is `true`, the taxpayer fails a **non-negotiable requirement** and cannot be granted exemption, regardless of how high their ML score is.

---

### 5.6 Example explanation using composite features

These composite features give intuitive explanations like:

> **Example explanation:**  
> Application rejected because of:  
> – **Low transparency score** (missing supplier TINs, landlord TINs, and incomplete director TINs)  
> – **High enforcement risk** (recent agency notice and under-estimation penalty in past 5 years)

---

## 6. How the model actually decides

The decision engine combines a **rule layer** and an **ML layer**.

### 6.1 Rule layer (non-negotiable legal rules)

The rule layer encodes conditions that reflect hard legal or policy constraints, for example:

- If `tin_active = false` → **Reject**.  
- If `is_wht_registered = false` and WHT is required for this taxpayer type → **Reject or manual review**.  
- If `has_outstanding_liability = true` and `on_approved_installment_plan = false` → **Manual review or Reject per policy**.  
- If `investigation_flag = true` and `last_investigation_recency_days < X` → **Manual review required**.  

**Example rule layer output:**

```json
{
  "rule_decision": "REVIEW_REQUIRED",
  "fatal_rule_violation": false,
  "rule_reasons": [
    "Outstanding liability but under installment plan",
    "Recent enforcement action 18 months ago"
  ]
}
```

The rule layer can produce three logical outcomes:

1. **Rule-based reject** (e.g. inactive TIN).  
2. **Rule-based approval** (rare, but possible if policy allows).  
3. **No fatal rules triggered → defer to ML + human thresholds.**

### 6.2 Machine-learning layer (probability of “safe to exempt”)

The ML model (e.g. gradient boosting, random forest, or logistic regression) takes the full feature vector:

- All checklist-derived features.  
- Composite scores (compliance, transparency, enforcement risk, stability).  

It outputs:

- `p_safe_to_exempt` – probability (0–1) that this taxpayer is low-risk to exempt.

**Example ML output:**

```json
{
  "p_safe_to_exempt": 0.92,
  "top_factors": [
    "High overall_compliance_score",
    "No recent enforcement actions",
    "High transparency_score",
    "Years_on_register > 5"
  ]
}
```

### 6.3 Combining rule and ML layers

The final decision logic might be:

- If `fatal_rule_violation = true` → **Reject**, regardless of `p_safe_to_exempt`.  
- Else if `p_safe_to_exempt >= 0.90` and no moderate risk rules triggered → **Auto-approve**.  
- Else if `0.60 <= p_safe_to_exempt < 0.90` or some non-fatal risk rules triggered → **Human officer review**.  
- Else → **Recommended reject**, subject to officer override.

**Example combined decision:**

```json
{
  "final_decision": "AUTO_APPROVE",
  "p_safe_to_exempt": 0.93,
  "rule_decision": "NO_FATAL_VIOLATION",
  "rule_reasons": [],
  "ml_reasons": [
    "High filing compliance ratio",
    "No enforcement actions in 5 years",
    "Directors all have valid TINs",
    "Consistent domestic tax payments > UGX 50m"
  ]
}
```

---

## 7. End-to-end decision flow

### 7.1 Step-by-step process

1. **Application submission**  
   - Taxpayer submits WHT exemption application via URA portal.

2. **Data retrieval**  
   - System loads all relevant data for the TIN (and associated directors) from core systems.

3. **Feature computation**  
   - Computes all base features for Q1–Q30.  
   - Computes composite indicators (compliance, transparency, enforcement risk, stability).  

4. **Rule evaluation**  
   - Applies hard rules and identifies any fatal legal violations.  

5. **ML scoring**  
   - For applications with no fatal rule violation, computes `p_safe_to_exempt`.  

6. **Decision synthesis**  
   - Combines rule and ML outputs to produce:
     - Auto-approve  
     - Auto-reject  
     - Route to officer with recommendation and reasons  

7. **Officer review (where applicable)**  
   - Officer sees:
     - Rule evaluation  
     - Model score and top contributing factors  
     - Checklist-style view of key features.  
   - Officer can confirm or override.

8. **Decision recording**  
   - Final decision + reasons + model version + feature snapshot logged immutably.

9. **Monitoring & revocation**  
   - Periodic recomputation of key features during exemption period.  
   - If thresholds are breached (e.g. new enforcement action, missed returns), system triggers revocation workflow or manual review.

### 7.2 End-to-end flow diagram

```text
[TAXPAYER APPLICATION]
        │
        ▼
[DATA LOAD → FEATURE ENGINEERING]
        │
        ▼
[HARD RULE EVALUATION]
   │           │
   │           ├─ Fatal violation → REJECT
   │           │
   │           └─ No fatal violation
   │
   ▼
[ML SCORING]
        │
        ▼
[COMBINED DECISION LOGIC]
   │          │           │
   │          │           └─ Route to Officer
   │          └─ Auto-Reject
   └─ Auto-Approve

        │
        ▼
[LOGGING & EXPLANATION]
        │
        ▼
[MONITORING & POSSIBLE REVOCATION]
```

---

## 8. Feature names and full data dictionary (core features)

### 8.1 Naming conventions

Pattern:

```text
wht_<group>_<short_description>
```

Where:

- `wht` = withholding tax model prefix.  
- `group` ∈ {`profile`, `vat`, `wht`, `paye`, `rental`, `profit`, `penalty`, `pay`, `enforce`, `dispute`, `waiver`, `investig`, `dir`, `composite`, `rule`}.  
- `short_description` is concise and descriptive.

### 8.2 Data dictionary fields

Each feature has:

- `feature_name` – exact column name.  
- `data_type` – boolean, int, double, string, date.  
- `granularity` – e.g. `tin`, (`tin`, `as_of_date`), (`tin`, `year`).  
- `source_table(s)` – source system tables/views.  
- `derived_from_checklist_question` – which Q (1–30) if applicable.  
- `definition` – human-readable description.  
- `calculation_logic` – formula or rule.

### 8.3 Full data dictionary for core features by group

#### 8.3.1 Registration & profile features (Q1–5)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_profile_has_all_director_tins | boolean | tin, as_of_date | dw_taxpayer_directors, dw_taxpayer_registry | Q1 | Whether all listed directors/associates have valid TINs | `true` if count(valid director TINs) = count(total directors) or total directors = 0 |
| wht_profile_director_tin_coverage_ratio | double | tin, as_of_date | dw_taxpayer_directors | Q1 | Share of directors/associates with valid TINs | `directors_with_valid_tin / total_directors` (0 if no directors) |
| wht_profile_tin_active | boolean | tin, as_of_date | dw_taxpayer_registry | Q2 | Whether taxpayer’s TIN is currently active | `true` if registry.status = 'ACTIVE' as of as_of_date |
| wht_profile_years_on_register | int | tin, as_of_date | dw_taxpayer_registry | Q2 | Full years since registration | `floor(datediff(as_of_date, registration_date) / 365)` |
| wht_profile_is_mature_taxpayer | boolean | tin, as_of_date | dw_taxpayer_registry | Q2 | Whether taxpayer has been registered ≥ 3 years | `wht_profile_years_on_register >= 3` |
| wht_profile_is_new_taxpayer | boolean | tin, as_of_date | dw_taxpayer_registry | Q3 | Whether taxpayer has been registered < 3 years | `wht_profile_years_on_register < 3` |
| wht_profile_plant_machinery_import_value_usd | double | tin, year | dw_customs_imports | Q3 | CIF value of plant & machinery imports for the year in USD | Sum of declared CIF values for relevant HS codes converted to USD |
| wht_profile_meets_investment_threshold | boolean | tin, year | dw_customs_imports | Q3 | Whether taxpayer imports plant & machinery ≥ USD 150,000 | `true` if wht_profile_plant_machinery_import_value_usd >= 150000 |
| wht_profile_has_other_income_tax_exemption | boolean | tin, as_of_date | dw_exemptions_registry | Q4 | Taxpayer has any other active income tax exemption | `true` if as_of_date is within any exemption period for tax type = income tax |
| wht_profile_last_update_date | date | tin | dw_taxpayer_registry | Q5 | Date taxpayer last updated registration profile | From registry field `last_update_date` |
| wht_profile_profile_update_recency_days | int | tin, as_of_date | dw_taxpayer_registry | Q5 | Days since last profile update | `datediff(as_of_date, wht_profile_last_update_date)` |
| wht_profile_is_profile_complete | boolean | tin, as_of_date | dw_taxpayer_registry | Q5 | Registration profile completeness flag (core fields present) | `true` if all mandatory fields (address, contacts, tax types, directors) are non-null |

---

#### 8.3.2 VAT / EFRIS / tax stamps / tax agent features (Q6–8)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_vat_is_vat_registered | boolean | tin, as_of_date | dw_tax_type_registrations | Q6 | VAT registration status | `true` if VAT present in tax type registrations at as_of_date |
| wht_vat_efris_usage_ratio | double | tin, year | dw_efris_invoices, dw_vat_returns | Q6 | Ratio of EFRIS-covered sales to declared VAT sales | `efris_total_sales_amount / vat_returns_total_sales_amount` (cap 0–1) |
| wht_vat_efris_fully_compliant | boolean | tin, year | dw_efris_invoices, dw_vat_returns | Q6 | EFRIS usage meets URA-defined threshold | `true` if wht_vat_efris_usage_ratio >= policy_threshold (e.g. 0.95) |
| wht_led_is_led_registered | boolean | tin, as_of_date | dw_tax_type_registrations | Q7 | Whether taxpayer is registered under LED or similar regime | `true` if LED tax type present |
| wht_led_tax_stamp_coverage_ratio | double | tin, year | dw_tax_stamps, dw_sales | Q7 | Share of stampable products that have tax stamps | `stamped_units / stampable_units` (0 if no stampable units) |
| wht_led_tax_stamp_noncompliance_incidents | int | tin, 5y_window | dw_tax_stamps, dw_enforcement_actions | Q7 | Number of recorded tax stamp non-compliance incidents in last 5 years | Count of incidents with type = stamp_noncompliance and date within 5 years of as_of_date |
| wht_profile_has_tax_agent | boolean | tin, as_of_date | dw_tax_agent_mandates | Q8 | Whether taxpayer has appointed a tax agent | `true` if active mandate record exists as of as_of_date |
| wht_profile_tax_agent_tin_valid | boolean | tin, as_of_date | dw_tax_agent_mandates, dw_taxpayer_registry | Q8 | Whether appointed tax agent has valid active TIN | Join agent TIN to registry and check status = 'ACTIVE' |
| wht_profile_tax_agent_risk_score | double | tin, as_of_date | dw_tax_agent_risk_scores | Q8 | Aggregate risk score for the appointed agent | Look up agent score (range and logic defined by URA) |

---

#### 8.3.3 WHT agent features (Q9–12)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_wht_is_wht_registered | boolean | tin, as_of_date | dw_tax_type_registrations | Q9 | Whether WHT is registered as a tax type | `true` if WHT tax type present for tin at as_of_date |
| wht_wht_is_designated_agent | boolean | tin, as_of_date | dw_wht_agents_registry | Q10 | Whether taxpayer is a designated WHT agent | `true` if tin exists in agent registry with active flag |
| wht_wht_returns_expected_12m | int | tin, as_of_date | dw_wht_agents_registry | Q11 | Number of WHT returns expected in last 12 months | Based on registration and filing frequency (e.g. 12 if monthly) |
| wht_wht_returns_filed_12m | int | tin, as_of_date | dw_wht_returns | Q11 | Number of WHT returns actually filed in last 12 months | Count of WHT returns with period_end within 12 months of as_of_date |
| wht_wht_filing_compliance_ratio | double | tin, as_of_date | dw_wht_agents_registry, dw_wht_returns | Q11 | Ratio of WHT returns filed vs expected | `wht_wht_returns_filed_12m / wht_wht_returns_expected_12m` (handle divide by zero) |
| wht_wht_avg_payment_delay_days | double | tin, as_of_date | dw_payments_ledger, dw_wht_returns | Q11 | Average days between WHT due date and payment date (last 12 months) | Average over WHT periods: `payment_date - due_date`, last 12 months |
| wht_wht_supplier_tin_coverage_ratio | double | tin, year | dw_wht_returns | Q12 | Share of local suppliers in WHT returns with valid TINs | `valid_supplier_tins / total_suppliers` |
| wht_wht_missing_supplier_tins_count | int | tin, year | dw_wht_returns | Q12 | Count of supplier lines without valid TINs | Count where supplier_tin is null or invalid |

---

#### 8.3.4 General filing & VAT quality features (Q13–15)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_profile_overall_filing_compliance_ratio | double | tin, as_of_date | dw_income_tax_returns, dw_vat_returns, dw_paye_returns, dw_wht_returns | Q13 | Combined filing compliance across all relevant tax types in last 12 months | `returns_filed_all / returns_expected_all` over the last 12 months |
| wht_profile_late_returns_last_12m | int | tin, as_of_date | same as above | Q13 | Count of returns filed after due date in last 12 months | Count where `filed_date > due_date` |
| wht_profile_max_days_late_return | int | tin, as_of_date | same as above | Q13 | Maximum days late among late returns in last 12 months | Max over `filed_date - due_date` |
| wht_vat_has_mixed_supplies | boolean | tin, year | dw_vat_returns | Q14 | Whether taxpayer has both exempt and taxable supplies in VAT | `true` if both supply types appear in returns |
| wht_vat_apportionment_flag | boolean | tin, year | dw_vat_returns, dw_audit_findings | Q14 | Whether VAT input apportionment is correctly applied | `true` if no adverse audit findings on apportionment in period |
| wht_vat_input_adjustments_last_12m | int | tin, as_of_date | dw_vat_returns, dw_audit_findings | Q14 | Count of input VAT adjustments due to apportionment errors in last 12 months | Count relevant adjustments in period |
| wht_vat_customer_tin_coverage_ratio | double | tin, year | dw_vat_returns | Q15 | Share of VAT customer lines with valid TINs | `valid_customer_tins / total_customer_lines` |
| wht_vat_customer_tin_mismatch_count | int | tin, year | dw_vat_returns, dw_taxpayer_registry | Q15 | Number of VAT customer TIN-name mismatches | Count where TIN/name pair does not match registry |

---

#### 8.3.5 PAYE & directors’ income features (Q16–18)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_paye_employee_count_declared | int | tin, month or year | dw_paye_returns | Q16 | Number of employees declared in PAYE returns | Sum of employees in PAYE returns for the period |
| wht_paye_total_remuneration_declared | double | tin, year | dw_paye_returns | Q16 | Total remuneration declared for PAYE in the year | Sum of taxable remuneration |
| wht_paye_remuneration_to_turnover_ratio | double | tin, year | dw_paye_returns, dw_income_tax_returns | Q16 | Ratio of declared remuneration to turnover | `total_remuneration / turnover` (where turnover from income tax returns) |
| wht_dir_directors_on_payroll_count | int | tin, year | dw_taxpayer_directors, dw_paye_returns | Q17 | Number of directors appearing in PAYE returns | Count director IDs that appear in PAYE employee list |
| wht_dir_directors_with_paye_tin | int | tin, year | dw_taxpayer_directors, dw_paye_returns | Q17 | Number of directors whose TIN appears on PAYE files | Count distinct director TINs in PAYE |
| wht_dir_directors_filing_personal_returns_ratio | double | tin, year | dw_taxpayer_directors, dw_personal_returns | Q18 | Share of directors who file personal income tax returns | `directors_with_personal_returns / total_directors` |
| wht_dir_directors_full_income_declared_flag | boolean | tin, year | dw_taxpayer_directors, dw_personal_returns, dw_paye_returns | Q18 | Flag indicating whether directors appear to declare all income (approximate check) | `true` if personal returns + PAYE + other known income is consistent within policy thresholds |

---

#### 8.3.6 Income mix & rental features (Q19–21)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_rental_has_rental_income | boolean | tin, year | dw_income_tax_returns | Q19 | Whether taxpayer declares rental income | `true` if rental income lines > 0 in return |
| wht_rental_has_business_income | boolean | tin, year | dw_income_tax_returns | Q19 | Whether taxpayer declares business income | `true` if business income lines > 0 |
| wht_rental_separate_rental_flag | boolean | tin, year | dw_income_tax_returns | Q19 | Whether rental income is reported separately from business income | `true` if rental is on separate schedules/sections as required |
| wht_risk_big_spend_no_tin_count | int | tin, year | dw_purchases, dw_supplier_registry | Q20 | Number of expenditure items > UGX 5m where supplier has no TIN | Count such purchases |
| wht_risk_big_spend_no_tin_total_amount | double | tin, year | dw_purchases | Q20 | Total amount of expenditure > UGX 5m to suppliers without TIN | Sum amounts where supplier TIN is null/invalid |
| wht_rental_landlord_tin_provided_flag | boolean | tin, year | dw_rental_schedules | Q21 | Whether landlord TINs are provided where required | `true` if all required rental entries have TINs |
| wht_rental_landlord_tin_valid_flag | boolean | tin, year | dw_rental_schedules, dw_taxpayer_registry | Q21 | Whether provided landlord TINs are valid and active | `true` if all landlord TINs match active entries in registry |

---

#### 8.3.7 Profitability, penalties & payments features (Q22–25)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_profit_years_of_consecutive_loss | int | tin, as_of_date | dw_income_tax_returns | Q22 | Number of consecutive loss years up to last return (max 3 for checklist) | Count of last consecutive years where profit_before_tax < 0 |
| wht_profit_loss_to_turnover_ratio | double | tin, year | dw_income_tax_returns | Q22 | Ratio of loss to turnover in the latest loss year | `abs(loss_amount) / turnover_amount` |
| wht_penalty_underestimation_flag_5y | boolean | tin, as_of_date | dw_penalties_ledger | Q23 | Whether taxpayer incurred under-estimation penalties in last 5 years | `true` if any penalty with type = underestimation and date in last 5 years |
| wht_penalty_underestimation_count_5y | int | tin, as_of_date | dw_penalties_ledger | Q23 | Count of under-estimation penalties in last 5 years | Count matching records |
| wht_penalty_underestimation_amount_5y | double | tin, as_of_date | dw_penalties_ledger | Q23 | Total under-estimation penalty amount in last 5 years | Sum of penalty amounts |
| wht_pay_tax_payment_compliance_ratio_12m | double | tin, as_of_date | dw_assessments, dw_payments_ledger | Q24 | Share of tax assessments paid by due date in last 12 months | `assessments_paid_on_time / total_assessments` over last 12 months |
| wht_pay_avg_payment_delay_days_12m | double | tin, as_of_date | dw_assessments, dw_payments_ledger | Q24 | Average days of payment delay across all taxes in last 12 months | Average of `payment_date - due_date` (only late ones or all, per design) |
| wht_pay_max_payment_delay_days_12m | int | tin, as_of_date | dw_assessments, dw_payments_ledger | Q24 | Maximum delay days in last 12 months | Max delay |
| wht_pay_is_small_taxpayer | boolean | tin, as_of_date | dw_taxpayer_registry | Q25 | Whether taxpayer is classified as “small taxpayer” | Based on URA segmentation logic |
| wht_pay_domestic_tax_paid_12m | double | tin, as_of_date | dw_payments_ledger | Q25 | Total domestic tax paid in last 12 months | Sum of domestic tax payments |
| wht_pay_meets_minimum_payment_threshold | boolean | tin, as_of_date | dw_payments_ledger, dw_taxpayer_registry | Q25 | For small taxpayers, whether domestic tax paid ≥ UGX 50m in last 12 months | `true` if wht_pay_is_small_taxpayer and wht_pay_domestic_tax_paid_12m >= 50_000_000 |

---

#### 8.3.8 Outstanding balances, enforcement, disputes, waivers, investigations (Q26–30)

| feature_name | data_type | granularity | source_table(s) | derived_from_checklist_question | definition | calculation_logic |
|--------------|-----------|------------|-----------------|----------------------------------|-----------|-------------------|
| wht_enforce_has_outstanding_liability | boolean | tin, as_of_date | dw_assessments, dw_payments_ledger | Q26 | Whether taxpayer has any unpaid tax liability as of as_of_date | `true` if outstanding_balance > 0 |
| wht_enforce_on_installment_plan_flag | boolean | tin, as_of_date | dw_installment_plans | Q26 | Whether outstanding liability is under an approved installment plan | `true` if active plan covers outstanding balance |
| wht_enforce_liability_to_turnover_ratio | double | tin, year | dw_assessments, dw_income_tax_returns | Q26 | Ratio of outstanding liability to annual turnover | `outstanding_balance / turnover` |
| wht_enforce_enforcement_actions_count_5y | int | tin, as_of_date | dw_enforcement_actions | Q27 | Number of enforcement actions in last 5 years | Count all enforcement actions in last 5 years |
| wht_enforce_recent_enforcement_flag | boolean | tin, as_of_date | dw_enforcement_actions | Q27 | Whether enforcement action occurred recently (e.g. last 12–24 months) | `true` if any enforcement_date within recent-period window |
| wht_dispute_disputed_balance_flag | boolean | tin, as_of_date | dw_disputes | Q28 | Whether taxpayer has an active ledger dispute with URA | `true` if dispute status = pending/open |
| wht_dispute_dispute_resolved_flag | boolean | tin, as_of_date | dw_disputes | Q28 | Whether last dispute has been resolved | `true` if last dispute has status = resolved/closed |
| wht_waiver_tax_waiver_count_5y | int | tin, as_of_date | dw_waiver_applications | Q29 | Number of tax waivers granted in last 5 years | Count of waivers granted in last 5 years |
| wht_waiver_tax_waiver_amount_5y | double | tin, as_of_date | dw_waiver_applications | Q29 | Total amount of waived tax in last 5 years | Sum of waived amounts |
| wht_investig_investigation_flag | boolean | tin, as_of_date | dw_investigations | Q30 | Whether taxpayer has been investigated by TID | `true` if any investigation record exists |
| wht_investig_investigation_count | int | tin, as_of_date | dw_investigations | Q30 | Number of investigations recorded | Count investigations |
| wht_investig_last_investigation_recency_days | int | tin, as_of_date | dw_investigations | Q30 | Days since last investigation was closed | `datediff(as_of_date, last_investigation_end_date)` |

---

#### 8.3.9 Composite and rule features (summary)

| feature_name | data_type | granularity | source_table(s) | definition | calculation_logic (high-level) |
|--------------|-----------|------------|-----------------|-----------|--------------------------------|
| wht_composite_overall_compliance_score | double | tin, as_of_date | wht_feature_store_wide (derived) | Combined index (0–100) summarising filing and payment compliance and WHT/VAT/PAYE behaviour | Weighted combination of normalised filing ratios, payment compliance, WHT behaviour, PAYE & VAT quality |
| wht_composite_enforcement_risk_score | double | tin, as_of_date | wht_feature_store_wide (derived) | Risk index (0–100) based on penalties, liabilities, enforcement, investigations | Weighted combination of penalty, liability, enforcement, investigation features |
| wht_composite_transparency_score | double | tin, as_of_date | wht_feature_store_wide (derived) | Index (0–100) of how visible taxpayer and counterparties are | Weighted combination of TIN coverage features and director/counterparty completeness |
| wht_composite_stability_score | double | tin, as_of_date | wht_feature_store_wide (derived) | Index (0–100) of business stability | Weighted combination of years on register, loss patterns, income mix, payments |
| wht_rule_any_fatal_legal_failure | boolean | tin, as_of_date | wht_feature_store_wide (derived) | Flag for non-negotiable legal rule failure | `true` if any hard rule condition is violated (inactive TIN, severe enforcement, etc.) |

---

## 9. Spark/Sparkflows feature pipeline

This section describes how to implement the feature pipeline using Spark/Sparkflows from raw URA tables to a feature store table.

### 9.1 Assumed raw tables/views

Typical data warehouse tables might include:

- `dw_taxpayer_registry`  
- `dw_taxpayer_directors`  
- `dw_tax_type_registrations`  
- `dw_income_tax_returns`  
- `dw_vat_returns`  
- `dw_paye_returns`  
- `dw_wht_returns`  
- `dw_wht_agents_registry`  
- `dw_efris_invoices`  
- `dw_tax_stamps`  
- `dw_assessments`  
- `dw_payments_ledger`  
- `dw_penalties_ledger`  
- `dw_enforcement_actions`  
- `dw_waiver_applications`  
- `dw_investigations`  
- `dw_disputes`

Target:

- A feature store table, e.g. `wht_feature_store_wide`, with **one row per (`tin`, `as_of_date`)** and columns for all features.

### 9.2 Main Sparkflows pipeline structure

```text
FLOW: WHT_FEATURES_MAIN

[1] Load Core Dimensions
    ├─ Load dw_taxpayer_registry
    ├─ Load dw_tax_type_registrations
    ├─ Load dw_taxpayer_directors

[2] Load Behavioural Fact Tables
    ├─ Load dw_income_tax_returns
    ├─ Load dw_vat_returns
    ├─ Load dw_paye_returns
    ├─ Load dw_wht_returns
    ├─ Load dw_wht_agents_registry
    ├─ Load dw_efris_invoices
    ├─ Load dw_tax_stamps
    ├─ Load dw_assessments
    ├─ Load dw_payments_ledger
    ├─ Load dw_penalties_ledger
    ├─ Load dw_enforcement_actions
    ├─ Load dw_waiver_applications
    ├─ Load dw_investigations
    ├─ Load dw_disputes

[3] Standardisation & Join Keys
    ├─ Clean TIN formats
    ├─ Standardise dates & currencies
    ├─ Build master taxpayer dimension

[4] Feature Subflows (per group)
    ├─ SUBFLOW_PROFILE_FEATURES
    ├─ SUBFLOW_VAT_EFRIS_FEATURES
    ├─ SUBFLOW_WHT_AGENT_FEATURES
    ├─ SUBFLOW_PAYE_DIR_FEATURES
    ├─ SUBFLOW_PROFIT_PENALTY_PAY_FEATURES
    ├─ SUBFLOW_ENFORCEMENT_INVESTIGATION_FEATURES
    ├─ SUBFLOW_COMPOSITE_FEATURES

[5] Wide Feature Join
    ├─ Join all feature datasets on (tin, as_of_date)

[6] Write to Feature Store
    ├─ Save as wht_feature_store_wide (Hive/Delta, partitioned by as_of_date)
```

### 9.3 Example subflow: profile features

**SUBFLOW_PROFILE_FEATURES**

Inputs:

- `dw_taxpayer_registry`  
- `dw_taxpayer_directors`  
- Parameter: `as_of_date`

Steps:

1. Load registry and filter to relevant taxpayers.  
2. Compute `wht_profile_years_on_register` as `floor(datediff(as_of_date, registration_date)/365)`.  
3. Derive `wht_profile_is_mature_taxpayer` and `wht_profile_is_new_taxpayer`.  
4. Join directors and compute:
   - `total_directors`  
   - `directors_with_valid_tin`  
   - `wht_profile_director_tin_coverage_ratio`  
   - `wht_profile_has_all_director_tins`.  
5. Compute `wht_profile_profile_update_recency_days = datediff(as_of_date, wht_profile_last_update_date)`.  
6. Derive `wht_profile_is_profile_complete` from required fields.  
7. Output one row per (`tin`, `as_of_date`) with all `wht_profile_*` features.

### 9.4 Example subflow: WHT agent features

**SUBFLOW_WHT_AGENT_FEATURES**

Inputs:

- `dw_wht_agents_registry`  
- `dw_wht_returns`  
- `dw_payments_ledger`  
- Parameter: `as_of_date`

Steps:

1. Determine expected returns from agent registry (e.g. monthly frequency) → `wht_wht_returns_expected_12m`.  
2. Count filed WHT returns over last 12 months → `wht_wht_returns_filed_12m`.  
3. Compute `wht_wht_filing_compliance_ratio`.  
4. Compute `wht_wht_avg_payment_delay_days` using due vs payment dates.  
5. From supplier lines in WHT returns compute `wht_wht_supplier_tin_coverage_ratio` and `wht_wht_missing_supplier_tins_count`.  
6. Output one row per (`tin`, `as_of_date`) with all `wht_wht_*` features.

### 9.5 Example subflow: composite features

**SUBFLOW_COMPOSITE_FEATURES**

Inputs:

- Outputs from all previous subflows joined on (`tin`, `as_of_date`).

Steps:

1. Normalise core numeric features used in scores.  
2. Compute:
   - `wht_composite_overall_compliance_score`  
   - `wht_composite_enforcement_risk_score`  
   - `wht_composite_transparency_score`  
   - `wht_composite_stability_score`.  
3. Compute `wht_rule_any_fatal_legal_failure` based on agreed hard rules.  
4. Output composite and rule features per (`tin`, `as_of_date`).

### 9.6 Final wide feature join and storage

In the main flow:

1. Load all subflow outputs (profile, VAT/EFRIS, WHT agent, PAYE/directors, profit/penalty/payments, enforcement/investigation, composite).  
2. Perform left joins stepwise on (`tin`, `as_of_date`) to build a wide feature row.  
3. Add metadata columns:
   - `feature_generation_timestamp`  
   - `feature_version`  
   - `law_version` (e.g. “FinanceAct_2023_24”).  
4. Write out:

```text
TABLE wht_feature_store_wide
PARTITIONED BY (as_of_date)
```

5. Register feature store and columns in the governance layer (e.g. Apache Atlas), mapping each column to its data dictionary entry.

---

## 10. Future scaling and governance hooks (brief)

This design is intended as a baseline that can scale:

- **Across tax types**: VAT risk models, PAYE compliance models, refund risk models, etc.  
- **Across years**: New feature versions for each Finance Act or policy change; old versions frozen for appeals.  
- **Across vendors**: Clear feature names, data dictionaries, and pipelines allow multiple teams (including external vendors) to collaborate.

Core governance practices:

- Version control for features, models, and law versions.  
- Immutable logs of decisions, including feature snapshots and model versions at scoring time.  
- Regular monitoring of performance, fairness, and drift.  
- Joint change control between Legal, Policy, IT, and Domestic Taxes for any rule/model adjustment.
- 


## 11. Decision record (model output) schema

This section defines the JSON schema for **every WHT exemption scoring event** so that URA can fully replay and audit any decision later.

The design goals:

1. **Uniquely identify** each decision and the taxpayer/application.  
2. **Capture all context** needed to replay the decision:
   - Law/policy set and feature definitions in force at the time.
   - Model and rule-engine versions.
   - Feature values actually used.  
3. **Capture intermediate logic**:
   - Rule evaluations (per rule).
   - ML outputs (scores, bands, top features).  
4. **Capture the final decision**:
   - System recommendation.
   - Officer final decision and overrides.
   - Reason codes and human-readable explanations.  
5. **Support governance & analytics**:
   - Timestamps, environment, channel.
   - Appeal and monitoring hooks.

The top-level JSON has these main blocks:

- `identity`  
- `context`  
- `input_snapshot`  
- `rule_layer`  
- `ml_layer`  
- `combined_decision`  
- `explanation`  
- `audit_metadata`  

---

### 11.1 High-level JSON structure

At the top level:

```jsonc
{
  "decision_id": "UUID",
  "decision_type": "WHT_EXEMPTION_ELIGIBILITY",
  "version": {
    "model_version": "wht_model_v1.0.3",
    "rule_engine_version": "wht_rules_v2024_07",
    "feature_spec_version": "wht_features_v2.1",
    "law_version": "FinanceAct_2023_24"
  },
  "identity": { ... },
  "context": { ... },
  "input_snapshot": { ... },
  "rule_layer": { ... },
  "ml_layer": { ... },
  "combined_decision": { ... },
  "explanation": { ... },
  "audit_metadata": { ... }
}
```

---

### 11.2 Identity block

Identifies **which case** this record relates to.

```jsonc
"identity": {
  "tin": "1000123456",
  "taxpayer_name": "ABC MANUFACTURERS LTD",
  "application_id": "WHTEX-2024-000123",
  "application_channel": "ONLINE_PORTAL",      // or "BACKOFFICE", "BATCH"
  "application_period": {
    "start_date": "2024-07-01",
    "end_date": "2025-06-30"
  }
}
```

---

### 11.3 Context block

Captures the **operational context** of scoring.

```jsonc
"context": {
  "scoring_timestamp": "2024-08-20T10:32:45Z",
  "as_of_date": "2024-08-20",                 // feature calculation date
  "environment": "PRODUCTION",                // or "UAT", "SANDBOX"
  "requested_by_user": {
    "user_id": "OFFICER123",
    "user_role": "DOMESTIC_TAXES_OFFICER",
    "office_code": "KLA01"
  },
  "trigger_type": "INITIAL_APPLICATION",      // or "RENEWAL", "PERIODIC_MONITORING"
  "source_system": "eSERVICES_PORTAL"
}
```

---

### 11.4 Input snapshot (features + references)

The **frozen feature vector** and a pointer back to the feature store.

```jsonc
"input_snapshot": {
  "feature_store_ref": {
    "table": "wht_feature_store_wide",
    "tin": "1000123456",
    "as_of_date": "2024-08-20",
    "feature_row_id": "frow-1000123456-2024-08-20"
  },
  "features": {
    "wht_profile_tin_active": true,
    "wht_profile_years_on_register": 7,
    "wht_profile_has_all_director_tins": true,
    "wht_profile_director_tin_coverage_ratio": 1.0,
    "wht_profile_is_profile_complete": true,

    "wht_vat_is_vat_registered": true,
    "wht_vat_efris_usage_ratio": 0.97,
    "wht_vat_efris_fully_compliant": true,

    "wht_wht_is_wht_registered": true,
    "wht_wht_is_designated_agent": true,
    "wht_wht_filing_compliance_ratio": 1.0,
    "wht_wht_avg_payment_delay_days": 1.5,

    "wht_profile_overall_filing_compliance_ratio": 0.98,
    "wht_profile_late_returns_last_12m": 1,
    "wht_profile_max_days_late_return": 3,

    "wht_pay_tax_payment_compliance_ratio_12m": 0.99,
    "wht_pay_domestic_tax_paid_12m": 850000000.0,
    "wht_pay_meets_minimum_payment_threshold": true,

    "wht_enforce_has_outstanding_liability": false,
    "wht_enforce_enforcement_actions_count_5y": 0,

    "wht_investig_investigation_flag": false,

    "wht_composite_overall_compliance_score": 92.5,
    "wht_composite_enforcement_risk_score": 8.0,
    "wht_composite_transparency_score": 95.0,
    "wht_composite_stability_score": 88.0,

    "wht_rule_any_fatal_legal_failure": false
  }
}
```

This snapshot is what allows full **replay** of the decision.

---

### 11.5 Rule layer block

Encodes the **rule-engine outcome** and per-rule decisions.

```jsonc
"rule_layer": {
  "rule_engine_version": "wht_rules_v2024_07",
  "evaluation_timestamp": "2024-08-20T10:32:45Z",
  "overall_status": "NO_FATAL_VIOLATION",   // NO_FATAL_VIOLATION | FATAL_VIOLATION | REVIEW_REQUIRED
  "fatal_rule_violation": false,
  "rules": [
    {
      "rule_id": "R001_TIN_ACTIVE",
      "rule_name": "Active TIN required",
      "category": "REGISTRATION",
      "check_type": "HARD",
      "passed": true,
      "evidence_feature": "wht_profile_tin_active",
      "evidence_value": true,
      "threshold_or_condition": "value == true",
      "law_reference": "ITA s.XX",
      "comment": null
    },
    {
      "rule_id": "R010_NO_UNMANAGED_LIABILITY",
      "rule_name": "No unmanaged outstanding liabilities",
      "category": "LIABILITY",
      "check_type": "HARD",
      "passed": true,
      "evidence_feature": "wht_enforce_has_outstanding_liability",
      "evidence_value": false,
      "threshold_or_condition": "value == false OR on_installment_plan == true",
      "law_reference": "TPC s.YY",
      "comment": null
    },
    {
      "rule_id": "R040_RECENT_INVESTIGATION_REVIEW",
      "rule_name": "Recent investigation requires review",
      "category": "INVESTIGATION",
      "check_type": "SOFT",
      "passed": true,
      "evidence_feature": "wht_investig_investigation_flag",
      "evidence_value": false,
      "threshold_or_condition": "if investigation_flag == true and recency_days < 730 → REVIEW_REQUIRED",
      "law_reference": "Internal Policy WHT-INV-2023",
      "comment": null
    }
  ]
}
```

If a fatal rule is triggered, then:

- `overall_status = "FATAL_VIOLATION"`  
- `fatal_rule_violation = true`  

and that feeds straight into the combined decision.

---

### 11.6 ML layer block

Captures **model scores**, bands, and feature attributions.

```jsonc
"ml_layer": {
  "model_version": "wht_model_v1.0.3",
  "algorithm": "xgboost",
  "training_reference": {
    "training_dataset_id": "wht_train_2024Q1",
    "training_cutoff_date": "2024-03-31"
  },
  "scores": {
    "p_safe_to_exempt": 0.932,
    "margin_score": 2.15                    // optional calibrated log-odds or distance
  },
  "score_bands": {
    "risk_band": "LOW_RISK",               // e.g. LOW_RISK / MEDIUM_RISK / HIGH_RISK
    "band_definition_version": "wht_band_v1"
  },
  "top_features": [
    {
      "feature_name": "wht_composite_overall_compliance_score",
      "direction": "POSITIVE",
      "contribution": 0.35,                // relative contribution
      "value": 92.5
    },
    {
      "feature_name": "wht_composite_transparency_score",
      "direction": "POSITIVE",
      "contribution": 0.25,
      "value": 95.0
    },
    {
      "feature_name": "wht_enforce_enforcement_actions_count_5y",
      "direction": "NEGATIVE",
      "contribution": -0.10,
      "value": 0
    },
    {
      "feature_name": "wht_profile_years_on_register",
      "direction": "POSITIVE",
      "contribution": 0.08,
      "value": 7
    }
  ]
}
```

This block is what powers **explainability** to officers and taxpayers.

---

### 11.7 Combined decision block

Captures the **system recommendation**, the **officer’s decision**, and the final outcome.

```jsonc
"combined_decision": {
  "system_recommendation": {
    "decision": "AUTO_APPROVE",          // AUTO_APPROVE | AUTO_REJECT | REVIEW
    "decision_band": "LOW_RISK_APPROVE", // internal label
    "reason_codes": [
      "HIGH_COMPLIANCE_SCORE",
      "HIGH_TRANSPARENCY_SCORE",
      "NO_RECENT_ENFORCEMENT"
    ],
    "thresholds": {
      "fatal_rule_required": false,
      "min_safe_probability_for_auto_approve": 0.90,
      "max_enforcement_risk_for_auto_approve": 20
    }
  },
  "officer_review": {
    "review_required": false,
    "review_performed": false,
    "officer_id": null,
    "review_timestamp": null,
    "officer_decision": null,            // APPROVE / REJECT / REQUEST_INFO
    "override_flag": null,
    "override_reason_code": null,
    "override_free_text": null
  },
  "final_outcome": {
    "decision": "APPROVE",               // APPROVE / REJECT / PENDING
    "effective_start_date": "2024-07-01",
    "effective_end_date": "2025-06-30",
    "can_be_revoked": true,
    "revocation_conditions_profile": "WHT_EXEMPT_GENERIC_2024"
  }
}
```

If an officer **overrides** the system:

- `officer_review.review_required = true`  
- `officer_review.review_performed = true`  
- `officer_review.officer_decision = "REJECT"` (for example)  
- `officer_review.override_flag = true`  
- `officer_review.override_reason_code = "OFFICER_RISK_ASSESSMENT"`  
- `final_outcome.decision` follows the officer’s decision.

---

### 11.8 Explanation block

Human-readable text for officers and taxpayers.

```jsonc
"explanation": {
  "primary_explanation_officer": {
    "language": "en",
    "audience": "OFFICER",
    "summary": "Taxpayer meets all mandatory conditions and shows strong compliance and transparency.",
    "details": [
      "Overall compliance score is 92.5 (very high).",
      "Transparency score is 95.0 (all director, supplier, customer and landlord TINs are valid).",
      "No outstanding liabilities or enforcement actions in the last 5 years.",
      "TIN has been active for 7 years with consistent domestic tax payments above UGX 50m."
    ]
  },
  "primary_explanation_taxpayer": {
    "language": "en",
    "audience": "TAXPAYER",
    "summary": "Your withholding tax exemption application has been approved.",
    "details": [
      "You have been filing and paying your taxes on time.",
      "You provide valid TINs for your directors and most suppliers and customers.",
      "You have no unpaid tax liabilities or recent enforcement actions."
    ]
  },
  "explanation_version": "wht_explainer_v1"
}
```

If rejected, the text would highlight composites and rules behind the rejection, for example:

- “Low transparency score due to missing supplier TINs and landlord TINs.”  
- “High enforcement risk due to recent agency notice and under-estimation penalties.”

---

### 11.9 Audit metadata block

For traceability and replay.

```jsonc
"audit_metadata": {
  "created_at": "2024-08-20T10:32:45Z",
  "created_by_service": "wht_decision_engine",
  "upstream_trace_id": "trace-2f09cd21-97c8-4e82-9c47-5b975fbb99ef",
  "input_data_hash": "sha256:9af6...b1c",          // hash of features blob
  "config_hash": "sha256:f3d2...9aa",             // hash of config (rules + thresholds)
  "replay_supported": true,
  "replay_instructions": {
    "replay_pipeline": "wht_replay_pipeline_v1",
    "required_inputs": [
      "input_snapshot.features",
      "version.model_version",
      "version.rule_engine_version"
    ]
  },
  "appeal_reference": {
    "has_appeal": false,
    "appeal_id": null,
    "appeal_status": null
  }
}
```

- `input_data_hash` proves which feature vector was used.  
- `config_hash` proves which rules and thresholds applied at the time.  
- `replay_instructions` ties this to a technical pipeline that can re-run the logic.

---

### 11.10 Full example decision record (assembled)

A full example decision record, combining all blocks into one object:

```json
{
  "decision_id": "dec-0c9b4f9a-1b48-4f30-9b2f-7e14d5c12345",
  "decision_type": "WHT_EXEMPTION_ELIGIBILITY",
  "version": {
    "model_version": "wht_model_v1.0.3",
    "rule_engine_version": "wht_rules_v2024_07",
    "feature_spec_version": "wht_features_v2.1",
    "law_version": "FinanceAct_2023_24"
  },
  "identity": {
    "tin": "1000123456",
    "taxpayer_name": "ABC MANUFACTURERS LTD",
    "application_id": "WHTEX-2024-000123",
    "application_channel": "ONLINE_PORTAL",
    "application_period": {
      "start_date": "2024-07-01",
      "end_date": "2025-06-30"
    }
  },
  "context": {
    "scoring_timestamp": "2024-08-20T10:32:45Z",
    "as_of_date": "2024-08-20",
    "environment": "PRODUCTION",
    "requested_by_user": {
      "user_id": "OFFICER123",
      "user_role": "DOMESTIC_TAXES_OFFICER",
      "office_code": "KLA01"
    },
    "trigger_type": "INITIAL_APPLICATION",
    "source_system": "eSERVICES_PORTAL"
  },
  "input_snapshot": {
    "feature_store_ref": {
      "table": "wht_feature_store_wide",
      "tin": "1000123456",
      "as_of_date": "2024-08-20",
      "feature_row_id": "frow-1000123456-2024-08-20"
    },
    "features": {
      "wht_profile_tin_active": true,
      "wht_profile_years_on_register": 7,
      "wht_profile_has_all_director_tins": true,
      "wht_profile_director_tin_coverage_ratio": 1.0,
      "wht_profile_is_profile_complete": true,
      "wht_vat_is_vat_registered": true,
      "wht_vat_efris_usage_ratio": 0.97,
      "wht_vat_efris_fully_compliant": true,
      "wht_wht_is_wht_registered": true,
      "wht_wht_is_designated_agent": true,
      "wht_wht_filing_compliance_ratio": 1.0,
      "wht_wht_avg_payment_delay_days": 1.5,
      "wht_profile_overall_filing_compliance_ratio": 0.98,
      "wht_profile_late_returns_last_12m": 1,
      "wht_profile_max_days_late_return": 3,
      "wht_pay_tax_payment_compliance_ratio_12m": 0.99,
      "wht_pay_domestic_tax_paid_12m": 850000000.0,
      "wht_pay_meets_minimum_payment_threshold": true,
      "wht_enforce_has_outstanding_liability": false,
      "wht_enforce_enforcement_actions_count_5y": 0,
      "wht_investig_investigation_flag": false,
      "wht_composite_overall_compliance_score": 92.5,
      "wht_composite_enforcement_risk_score": 8.0,
      "wht_composite_transparency_score": 95.0,
      "wht_composite_stability_score": 88.0,
      "wht_rule_any_fatal_legal_failure": false
    }
  },
  "rule_layer": {
    "rule_engine_version": "wht_rules_v2024_07",
    "evaluation_timestamp": "2024-08-20T10:32:45Z",
    "overall_status": "NO_FATAL_VIOLATION",
    "fatal_rule_violation": false,
    "rules": [
      {
        "rule_id": "R001_TIN_ACTIVE",
        "rule_name": "Active TIN required",
        "category": "REGISTRATION",
        "check_type": "HARD",
        "passed": true,
        "evidence_feature": "wht_profile_tin_active",
        "evidence_value": true,
        "threshold_or_condition": "value == true",
        "law_reference": "ITA s.XX",
        "comment": null
      },
      {
        "rule_id": "R010_NO_UNMANAGED_LIABILITY",
        "rule_name": "No unmanaged outstanding liabilities",
        "category": "LIABILITY",
        "check_type": "HARD",
        "passed": true,
        "evidence_feature": "wht_enforce_has_outstanding_liability",
        "evidence_value": false,
        "threshold_or_condition": "value == false OR on_installment_plan == true",
        "law_reference": "TPC s.YY",
        "comment": null
      }
    ]
  },
  "ml_layer": {
    "model_version": "wht_model_v1.0.3",
    "algorithm": "xgboost",
    "training_reference": {
      "training_dataset_id": "wht_train_2024Q1",
      "training_cutoff_date": "2024-03-31"
    },
    "scores": {
      "p_safe_to_exempt": 0.932,
      "margin_score": 2.15
    },
    "score_bands": {
      "risk_band": "LOW_RISK",
      "band_definition_version": "wht_band_v1"
    },
    "top_features": [
      {
        "feature_name": "wht_composite_overall_compliance_score",
        "direction": "POSITIVE",
        "contribution": 0.35,
        "value": 92.5
      },
      {
        "feature_name": "wht_composite_transparency_score",
        "direction": "POSITIVE",
        "contribution": 0.25,
        "value": 95.0
      },
      {
        "feature_name": "wht_enforce_enforcement_actions_count_5y",
        "direction": "NEGATIVE",
        "contribution": -0.10,
        "value": 0
      }
    ]
  },
  "combined_decision": {
    "system_recommendation": {
      "decision": "AUTO_APPROVE",
      "decision_band": "LOW_RISK_APPROVE",
      "reason_codes": [
        "HIGH_COMPLIANCE_SCORE",
        "HIGH_TRANSPARENCY_SCORE",
        "NO_RECENT_ENFORCEMENT"
      ],
      "thresholds": {
        "fatal_rule_required": false,
        "min_safe_probability_for_auto_approve": 0.9,
        "max_enforcement_risk_for_auto_approve": 20
      }
    },
    "officer_review": {
      "review_required": false,
      "review_performed": false,
      "officer_id": null,
      "review_timestamp": null,
      "officer_decision": null,
      "override_flag": null,
      "override_reason_code": null,
      "override_free_text": null
    },
    "final_outcome": {
      "decision": "APPROVE",
      "effective_start_date": "2024-07-01",
      "effective_end_date": "2025-06-30",
      "can_be_revoked": true,
      "revocation_conditions_profile": "WHT_EXEMPT_GENERIC_2024"
    }
  },
  "explanation": {
    "primary_explanation_officer": {
      "language": "en",
      "audience": "OFFICER",
      "summary": "Taxpayer meets all mandatory conditions and shows strong compliance and transparency.",
      "details": [
        "Overall compliance score is 92.5 (very high).",
        "Transparency score is 95.0 (all director, supplier, customer and landlord TINs are valid).",
        "No outstanding liabilities or enforcement actions in the last 5 years.",
        "TIN has been active for 7 years with consistent domestic tax payments above UGX 50m."
      ]
    },
    "primary_explanation_taxpayer": {
      "language": "en",
      "audience": "TAXPAYER",
      "summary": "Your withholding tax exemption application has been approved.",
      "details": [
        "You have been filing and paying your taxes on time.",
        "You provide valid TINs for your directors and most suppliers and customers.",
        "You have no unpaid tax liabilities or recent enforcement actions."
      ]
    },
    "explanation_version": "wht_explainer_v1"
  },
  "audit_metadata": {
    "created_at": "2024-08-20T10:32:45Z",
    "created_by_service": "wht_decision_engine",
    "upstream_trace_id": "trace-2f09cd21-97c8-4e82-9c47-5b975fbb99ef",
    "input_data_hash": "sha256:9af6...b1c",
    "config_hash": "sha256:f3d2...9aa",
    "replay_supported": true,
    "replay_instructions": {
      "replay_pipeline": "wht_replay_pipeline_v1",
      "required_inputs": [
        "input_snapshot.features",
        "version.model_version",
        "version.rule_engine_version"
      ]
    },
    "appeal_reference": {
      "has_appeal": false,
      "appeal_id": null,
      "appeal_status": null
    }
  }
}
```
- **Replaying** the decision using the same model + rules + features.  
- **Auditing** the decision in detail (inputs, logic, outputs).  
- **Explaining** the decision to officers and taxpayers.  
- **Supporting appeals** and future policy/model evolution.