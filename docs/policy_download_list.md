# PolicyLens — Document Download List

> **Purpose:** Curated list of documents for PolicyLens, organized by priority.
> **Date:** July 1, 2026
> **Usage:** Feed this to Devin along with a Python download script.

---

## PRIORITY 1: MVP Documents (Download First — Required for July 2 Demo)

These 4 documents go into the `docs\` folder and are used by the ingestion pipeline.

| # | Document | Filename | URL |
|---|----------|----------|-----|
| 1 | South Africa — POPIA (Protection of Personal Information Act, 2013) | `south_africa_popia.pdf` | https://www.gov.za/sites/default/files/gcis_document/201409/3706726-11act4of2013protectionofpersonalinforcorrect.pdf |
| 2 | Kenya — Data Protection Act No. 24 of 2019 | `kenya_dpa_2019.pdf` | https://kdic.go.ke/sites/default/files/2021-07/TheDataProtectionAct__No24of2019.pdf |
| 3 | Uganda — Data Protection and Privacy Act No. 9 of 2019 | `uganda_dppa_2019.pdf` | https://ict.go.ug/wp-content/uploads/2019/03/Data-Protection-and-Privacy-Act-2019.pdf |
| 4 | AU Malabo Convention on Cyber Security and Personal Data Protection (2014) | `au_malabo_convention.pdf` | https://ccdcoe.org/uploads/2018/11/AU-270614-CSConvention.pdf |

**Download location:** `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\`

---

## PRIORITY 2: Continental / Regional Frameworks (Download for Future Ingestion)

These are the continental and regional policy frameworks identified in Verena's spreadsheet. They will be useful for expanding PolicyLens beyond the MVP.

| # | Document | Filename | URL |
|---|----------|----------|-----|
| 5 | STISA 2034 — AU Science, Technology and Innovation Strategy | `au_stisa_2034.pdf` | https://au.int/sites/default/files/documents/45087-doc-AU_STISA_2025-2034_Strategy_ENGLISH.pdf |
| 6 | STISA 2034 — Draft strategy (alternative source) | `au_stisa_2034_draft.pdf` | https://dataalliance.africa/wp-content/uploads/STISA-2034-Strategy.pdf |
| 7 | STISA 2024 — Previous AU STI strategy (for reference) | `au_stisa_2024.pdf` | https://au.int/sites/default/files/newsevents/workingdocuments/33178-wd-stisa-english_-_final.pdf |
| 8 | AU Biodiversity Strategy and Action Plan 2023-2030 | `au_biodiversity_strategy_2023.pdf` | https://au.int/sites/default/files/documents/44075-doc-AU_Biodiversity_Strategy_12_08_2024.pdf |
| 9 | AU Practical Guidelines on ABS / Nagoya Protocol | `au_abs_nagoya_guidelines.pdf` | https://absch.cbd.int/api/v2013/documents/ACA06BA7-2ED4-19C0-F096-883C14068E94/attachments/AUPracticalGuidelinesOnABS_20150215_Druck.pdf |

**Download location:** `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\future\`

---

## PRIORITY 3: Academic & Research Papers (Download for Reference and Potential Ingestion)

These papers are directly relevant to the PolicyLens use case — they analyze African data protection laws, cross-border data sharing, and health data governance. Some could even be ingested into the system as supplementary context.

**From Verena's Source Register:**

| # | Document | Filename | URL |
|---|----------|----------|-----|
| 10 | Springer/HRPS — Data protection legislation in Africa (analysis of 37 laws) | `springer_data_protection_africa.pdf` | https://link.springer.com/content/pdf/10.1186/s12961-024-01230-7.pdf |
| 11 | ECDPM Discussion Paper 379 — Cross-border data flows in Africa | `ecdpm_cross_border_data_flows.pdf` | https://ecdpm.org/application/files/8417/3202/4662/Cross-Border-Data-Flows-Africa-Continental-Ambitions-Political-Realities-ECDPM-Discussion-Paper-379-2024.pdf |

**From Consensus Academic Search (highly relevant open-access papers):**

| # | Document | Filename | Why It Matters | URL |
|---|----------|----------|----------------|-----|
| 12 | Cross-border data sharing for research in Africa: analysis of 12 jurisdictions (Staunton et al., 2025) | `staunton_2025_cross_border_12_countries.pdf` | Analyzes the exact same countries and questions as PolicyLens — from the DS-I Africa Law group behind datalaw.bot. Covers SA, Kenya, Uganda and 9 others. | https://academic.oup.com/jlb/article-pdf/12/1/lsaf003/62776710/lsaf003.pdf |
| 13 | The regulation of health data sharing in Africa: comparative study of 5 countries (Nienaber McKay et al., 2024) | `nienaber_2024_health_data_sharing_regulation.pdf` | Compares health data sharing regulations across 5 African countries — directly relevant to our compliance demo questions. | https://repository.up.ac.za/server/api/core/bitstreams/f057a0c0-46c5-413c-8108-ec67295e9431/content |
| 14 | De-identification, anonymisation, pseudonymisation across 12 African nations (Edgcumbe et al., 2025) | `edgcumbe_2025_deidentification_africa.pdf` | Shows how the same legal concepts use different terminology across countries — exactly the kind of mismatch our query rewriter needs to handle. | https://pmc.ncbi.nlm.nih.gov/articles/PMC11932073/pdf/lsae029.pdf |
| 15 | AU Malabo Convention: Challenges and Future Directions (Bouke et al., 2023) | `bouke_2023_malabo_convention_challenges.pdf` | Deep analysis of the Malabo Convention implementation challenges — directly relevant since this is one of our 4 MVP documents. | https://arxiv.org/pdf/2305.13662.pdf |
| 16 | Africa's Data Privacy Puzzle: 17 countries (Kaddu et al., 2024) | `kaddu_2024_africa_data_privacy_puzzle.pdf` | Analysis of data privacy laws and compliance in 17 African countries — useful for expanding beyond MVP. | https://journals.udsm.ac.tz/index.php/lj/article/view/6226/5020 |
| 17 | Data sharing governance in sub-Saharan Africa during public health emergencies (Brand et al., 2022) | `brand_2022_data_sharing_emergencies.pdf` | Covers emergency data sharing governance — relevant for pathogen data questions the team raised. | https://www.scielo.org.za/pdf/sajs/v118n11-12/14.pdf |
| 18 | AU Agenda 2063 and Data Protection (Eyitayo, 2024) | `eyitayo_2024_au_agenda_2063_data_protection.pdf` | Overview of Malabo Convention ratification status and enforcement across Africa. | https://journals.stecab.com/index.php/jahss/article/download/1005/434/6097 |

**Download location:** `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\reference\`

**Note on paper #12 (Staunton et al.) and #14 (Edgcumbe et al.):** These OUP PDF links are paywalled and return 403 for unauthenticated requests. The script will flag them as failed. Both articles are available on PubMed Central as HTML for manual reading:
- Staunton: https://pmc.ncbi.nlm.nih.gov/articles/PMC11065056/
- Edgcumbe: https://pmc.ncbi.nlm.nih.gov/articles/PMC11932073/

**Note on paper #16:** This is the same paper Sumir shared in the email thread (the Google redirect URL). It's from the University of Dar es Salaam Law Journal.

---

## Notes for Devin

### Download Script Requirements

1. Create subdirectories if they don't exist:
   - `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\` (MVP documents)
   - `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\future\` (continental frameworks)
   - `C:\Users\ic\OneDrive\Desktop\PolicyBot\docs\reference\` (research papers)

2. Use `requests` library with a proper User-Agent header (some government sites block default Python user agents).

3. Verify each download by checking:
   - HTTP status code is 200
   - File size is greater than 10KB (to catch empty/error pages)
   - File starts with `%PDF` header (to confirm it's actually a PDF)

4. If a URL fails, log the error and continue — don't stop the entire script.

5. Use `python download_docs.py --no-verify-ssl` for sites with self-signed or expired certificates (e.g. `kdic.go.ke`, `journals.udsm.ac.tz`).

6. Print a summary at the end showing which files downloaded successfully and which failed.

7. **PRIORITY 1 documents are critical.** If any of these fail, flag it clearly — the MVP cannot proceed without them.

---

*Curated from Verena Ras's ABI Data Governance spreadsheet (Source_Register sheet), Consensus academic search, and verified against public availability.*