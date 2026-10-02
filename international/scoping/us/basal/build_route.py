"""Write route.csv: the US regulatory and coverage route for degludec, glargine 300, Fiasp and
Lyumjev. The US has no national health technology assessment, so the record is (a) FDA approval
history from Drugs@FDA documents and (b) public evidence of formulary treatment by the large
pharmacy benefit managers, plus the Medicare Part D insulin cost-sharing measures.

Every quote below was copied from the text version of the saved capture named in the same row
(captures/*.txt, produced with pdftotext -layout or by stripping HTML). Dates are those of the
document or decision. Rows for formulary lists are in FORMULARY, filled from the captures saved
under captures/ by the formulary search; where a list was checked and a product was absent, the
row says so.

Run from this folder: python3 build_route.py
"""
import csv

FDA = "US FDA (CDER)"
DAF = "https://www.accessdata.fda.gov/drugsatfda_docs/"

ROWS = [
    # degludec
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="Complete Response (approval refused): CV-risk meta-analysis and manufacturing deficiencies",
         date="2013-02-08",
         quote="On 8 February 2013 the two applications received a Complete Response for manufacturing "
               "deficiencies ... and because results of a meta-analysis comparing cardiovascular risk (CV-risk) "
               "between insulin degludec and comparators ... suggested CV-risk was higher in patients randomized "
               "to insulin degludec.",
         url=DAF + "nda/2015/203313Orig1s000_203314Orig1s000SumR.pdf",
         capture="captures/fda_tresiba_summary_review_2015.txt"),
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="CRL required a dedicated CV outcomes trial versus glargine",
         date="2013-02-08",
         quote="In the Complete Response letter, the Agency asked the applicant to exclude the possibility that "
               "insulin degludec was associated with excess CV-risk by comparing degludec to glargine ... in a "
               "dedicated, double-blind, cardiovascular outcomes trial.",
         url=DAF + "nda/2015/203313Orig1s000_203314Orig1s000SumR.pdf",
         capture="captures/fda_tresiba_summary_review_2015.txt"),
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="Class 2 resubmission with DEVOTE interim analysis",
         date="2015-03-26",
         quote="Novo Nordisk filed Class 2 re-submissions for the Tresiba and Ryzodeg 70/30 applications on "
               "26 March 2015 with interim results from their dedicated cardiovascular outcomes trial (DEVOTE trial)",
         url=DAF + "nda/2015/203313Orig1s000_203314Orig1s000SumR.pdf",
         capture="captures/fda_tresiba_summary_review_2015.txt"),
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="Approved (NDA 203314; Drugs@FDA class Type 1, new molecular entity) on DEVOTE interim data",
         date="2015-09-25",
         quote="Based on the interim analyses of the Devote trial, I conclude that the Applicant has demonstrated "
               "that insulin degludec is not associated with an excess CV-risk increase 80% that of glargine.",
         url=DAF + "nda/2015/203313Orig1s000_203314Orig1s000SumR.pdf",
         capture="captures/fda_tresiba_summary_review_2015.txt"),
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="Approval letter",
         date="2015-09-25",
         quote="We have completed our review of this application, as amended. It is approved, effective on the "
               "date of this letter",
         url=DAF + "appletter/2015/203314Orig1s000ltr.pdf",
         capture="captures/fda_tresiba_approval_letter_2015.txt"),
    dict(product="Tresiba (insulin degludec)", body=FDA,
         decision="Label supplement S-008 adds DEVOTE final results, including lower severe hypoglycaemia",
         date="2018-03-26",
         quote="The incidence of severe hypoglycemia was lower in the TRESIBA group as compared to the insulin "
               "glargine U-100 group (Table 16).",
         url=DAF + "label/2018/203314s008lbl.pdf",
         capture="captures/fda_tresiba_s008_label_2018.txt"),
    # glargine 300
    dict(product="Toujeo (insulin glargine 300 U/ml)", body=FDA,
         decision="Approved (NDA 206538; Drugs@FDA class Type 5, new formulation)",
         date="2015-02-25",
         quote="Although there is relatively sparse 1-year data the active ingredient is not a new molecular "
               "entity and the exposure number and duration were judged to be sufficient for filing.",
         url=DAF + "nda/2015/206538Orig1s000SumR.pdf",
         capture="captures/fda_toujeo_summary_review_2015.txt"),
    dict(product="Toujeo (insulin glargine 300 U/ml)", body=FDA,
         decision="Approval letter",
         date="2015-02-25",
         quote="We have completed our review of this application, as amended. It is approved, effective on the "
               "date of this letter",
         url=DAF + "appletter/2015/206538Orig1s000ltr.pdf",
         capture="captures/fda_toujeo_approval_letter_2015.txt"),
    # Fiasp
    dict(product="Fiasp (faster insulin aspart)", body=FDA,
         decision="Complete Response: clinical pharmacology (bioanalytical method) and immunogenicity",
         date="2016-10-07",
         quote="The first cycle NDA for FIASP was issued a Complete Response (CR) on 7 Oct 2016 for deficiencies "
               "pertaining to Clinical Pharmacology and Immunogenicity.",
         url=DAF + "nda/2017/208751Orig1s000SumR.pdf",
         capture="captures/fda_fiasp_summary_review_2017.txt"),
    dict(product="Fiasp (faster insulin aspart)", body=FDA,
         decision="Approved (NDA 208751; Drugs@FDA class Type 5, new formulation)",
         date="2017-09-29",
         quote="The product under review in this NDA (proposed tradename FIASP) is a new formulation of insulin "
               "aspart ... However, NovoLog and FIASP still have the same active ingredient.",
         url=DAF + "nda/2017/208751Orig1s000SumR.pdf",
         capture="captures/fda_fiasp_summary_review_2017.txt"),
    dict(product="Fiasp (faster insulin aspart)", body=FDA,
         decision="Approval letter",
         date="2017-09-29",
         quote="We acknowledge receipt of your amendment dated March 29, 2017, which constituted a complete "
               "response to our October 7, 2016, action letter. ... It is approved, effective on the date of this letter",
         url=DAF + "appletter/2017/208751Orig1s000ltr.pdf",
         capture="captures/fda_fiasp_approval_letter_2017.txt"),
    # Lyumjev
    dict(product="Lyumjev (insulin lispro-aabc)", body=FDA,
         decision="Approved (BLA 761109 under PHS Act 351(a); Drugs@FDA class Type 5, new formulation)",
         date="2020-06-15",
         quote="We also refer to our approval letter dated June 15, 2020 ... The effective approval date will "
               "remain June 15, 2020, the date of the original approval letter.",
         url=DAF + "appletter/2020/761109Orig1s000_replacement_ltr.pdf",
         capture="captures/fda_lyumjev_approval_letter_2020.txt"),
]

CVS = "CVS Caremark formulary drug removals list (inferred Standard Formulary)"
CVSU = "https://web.archive.org/web/{}/https://www.caremark.com/portal/asset/Formulary_Exclusion_Drug_List.pdf"
ESI = "Express Scripts National Preferred Formulary exclusions"
ESIU = "https://web.archive.org/web/{}/https://www.express-scripts.com/{}"
CMS = "CMS Part D Senior Savings Model"
IRA = "CMS Part D insulin cost-sharing cap (Inflation Reduction Act)"


def F(product, body, decision, date, quote, url, capture):
    return dict(product=product, body=body, decision=decision, date=date, quote=quote, url=url,
                capture="captures/" + capture)


# Quotes from the two-column PBM lists are given as "excluded ... preferred alternative" parts,
# each verified against the capture text; the column layout is lost in text extraction.
# Wayback URLs point at the capture date or year; the list's own effective year is in `date`.
FORMULARY = [
    F("Tresiba; Toujeo", CVS, "not listed (only rapid-acting insulin row)", "2016-01-01",
      "This list is effective January 1, 2016",
      "https://web.archive.org/web/20151106012118/http://www.caremark.com:80/portal/asset/Formulary_Exclusion_Drug_List_OE.pdf",
      "cvs_formulary_exclusion_drug_list_OE_wb20151106012118.txt"),
    F("Toujeo", CVS, "excluded (with Lantus); Basaglar, Levemir, Tresiba preferred", "2017-01-01",
      "LANTUS ... BASAGLAR †, LEVEMIR, TRESIBA ... TOUJEO", CVSU.format("20170209163929"),
      "cvs_formulary_exclusion_drug_list_wb20170209163929.txt"),
    F("Tresiba", CVS, "preferred alternative to excluded Lantus and Toujeo", "2017-01-01",
      "BASAGLAR †, LEVEMIR, TRESIBA", CVSU.format("20170209163929"),
      "cvs_formulary_exclusion_drug_list_wb20170209163929.txt"),
    F("Fiasp; Lyumjev", CVS, "not listed", "2018-01",
      "(product absent from list)", CVSU.format("20180129132434"),
      "cvs_formulary_exclusion_drug_list_wb20180129132434.txt"),
    F("Toujeo", CVS, "excluded; Tresiba preferred", "2020-10",
      "Long Acting Insulins TOUJEO TRESIBA", CVSU.format("20201020025549"),
      "cvs_formulary_exclusion_drug_list_wb20201020025549.txt"),
    F("Fiasp", CVS, "preferred alternative to excluded Apidra and Humalog (lists 2020-07 to 2023-10)", "2020-10",
      "APIDRA FIASP, NOVOLOG HUMALOG", CVSU.format("20201020025549"),
      "cvs_formulary_exclusion_drug_list_wb20201020025549.txt"),
    F("Toujeo; Tresiba; Lyumjev", CVS, "not excluded (insulin removals reduced to Lantus, Apidra, Humalog)", "2021-04",
      "Long Acting Insulins - First Generation", CVSU.format("20210421204408"),
      "cvs_formulary_exclusion_drug_list_wb20210421204408.txt"),
    F("Tresiba; Toujeo; Fiasp; Lyumjev", CVS, "removals list replaced by Performance Drug List", "2024-01-01",
      "effective January 1, 2024, information on formulary drug removals is available in the Performance Drug List",
      CVSU.format("20240302185442"), "cvs_formulary_exclusion_drug_list_wb20240302185442.txt"),
    F("Tresiba; Toujeo; Fiasp; Lyumjev", "CVS Caremark Performance Drug List, Standard Opt Out",
      "all four listed as preferred insulins", "2026-10",
      "LYUMJEV ... TOUJEO ... TRESIBA ... FIASP",
      "https://www.caremark.com/content/dam/enterprise/headless/caremark/cmk/en/assets/clinical/drug-list-bob/PerformanceDL_StandardOptOut.pdf",
      "cvs_performance_drug_list_standard_optout_2026.txt"),
    F("Tresiba; Toujeo", ESI, "not listed", "2017",
      "(product absent from list)",
      ESIU.format("20161110182617", "art/open_enrollment/DrugListExclusionsAndAlternatives.pdf"),
      "esi_npf_exclusions_2017.txt"),
    F("Fiasp", ESI, "excluded; Humalog preferred", "2019",
      "ADMELOG, APIDRA, FIASP, INSULIN LISPRO, NOVOLOG HUMALOG",
      ESIU.format("20190426160204", "art/pdf/Preferred_Drug_List_Exclusions2019.pdf"),
      "esi_npf_exclusions_2019.txt"),
    F("Fiasp; Lyumjev", ESI, "Fiasp excluded; Humalog and Lyumjev preferred", "2021",
      "ADMELOG, APIDRA, FIASP, INSULIN ASPART, ... HUMALOG, LYUMJEV",
      ESIU.format("20201028093921", "art/pdf/NPF_Preferred_Formulary_Exclusions2021.pdf"),
      "esi_npf_exclusions_2021.txt"),
    F("Toujeo; Tresiba", ESI, "preferred alternatives to excluded Semglee (from 2021-07-01)", "2021-07-01",
      "SEMGLEE LANTUS, LEVEMIR, TOUJEO, TRESIBA",
      ESIU.format("20210408221608", "art/pdf/NPF_exclusions_204612.pdf"),
      "esi_npf_exclusions_204612_2021.txt"),
    F("Toujeo; Tresiba", ESI, "preferred; Lantus and unbranded degludec excluded", "2023",
      "INSULIN DEGLUDEC, INSULIN GLARGINE (BY WINTHROP), ... LEVEMIR, SEMGLEE (YFGN), TOUJEO, TRESIBA",
      ESIU.format("20230130073130", "art/pdf/NPF_Preferred_Formulary_Exclusions2023.pdf"),
      "esi_npf_exclusions_2023.txt"),
    F("Fiasp; Lyumjev", ESI, "Fiasp excluded; Lyumjev preferred", "2023",
      "ADMELOG, AFREZZA, APIDRA, FIASP, INSULIN ASPART, ... HUMALOG, LYUMJEV",
      ESIU.format("20230130073130", "art/pdf/NPF_Preferred_Formulary_Exclusions2023.pdf"),
      "esi_npf_exclusions_2023.txt"),
    F("Tresiba; Toujeo; Fiasp; Lyumjev", ESI,
      "Tresiba, Toujeo, Lyumjev preferred; Fiasp excluded; unbranded degludec and glargine U-300 excluded", "2026",
      "U-100: ADMELOG, APIDRA, FIASP, ... LYUMJEV KWIKPEN & VIAL, ... SEMGLEE (YFGN), TRESIBA ... U-200: TRESIBA ... U-200: INSULIN DEGLUDEC",
      ESIU.format("20251105023258", "pdf/formulary/NPF_Preferred_Formulary_Exclusions2026.pdf"),
      "esi_npf_exclusions_2026.txt"),
    F("all insulins", CMS, "model announced: $35 for a month of a broad set of plan-formulary insulins", "2020-03-11",
      "a thirty-day supply of a broad set of plan-formulary insulins costs no more than $35",
      "https://www.cms.gov/newsroom/fact-sheets/part-d-senior-savings-model",
      "cms_senior_savings_model_factsheet_2020.txt"),
    F("Tresiba; Toujeo; Fiasp", CMS, "participating insulin, CY2021 NDC list (Lyumjev not yet approved)", "2020-03-23",
      "Tresiba® FlexTouch® U-100 Pen ... Toujeo® SoloStar® Pen ... Fiasp® FlexTouch® Pen",
      "https://web.archive.org/web/20200325141925/https://innovation.cms.gov/Files/x/partd-seniordav-ndclist.pdf",
      "cms_ssm_ndc_list_2021.txt"),
    F("Lyumjev", CMS, "participating insulin, CY2022 NDC list", "2022-11-02",
      "Lyumjev™ Kwikpen® U-100 Pen",
      "https://www.cms.gov/priorities/innovation/media/document/partd-seniorsav-ndclist-2022",
      "cms_ssm_ndc_list_2022.txt"),
    F("all insulins", CMS, "model ended", "2023-12-31",
      "This voluntary Model began on January 1, 2021 and concluded on December 31, 2023.",
      "https://www.cms.gov/priorities/innovation/innovation-models/part-d-savings-model",
      "cms_senior_savings_model_page_2026.txt"),
    F("Tresiba; Toujeo; Fiasp; Lyumjev (when on formulary)", IRA,
      "$35 monthly cost-sharing cap on each covered insulin from 2023-01-01; formulary rules unchanged", "2022-09-26",
      "cost sharing for a one-month supply of each covered insulin product must not exceed $35 ... "
      "existing formulary requirements under § 423.120(b) regarding formulary review and approval for insulin "
      "products otherwise remain unchanged for CY 2023",
      "https://www.cms.gov/files/document/irainsulinvaccinesmemo09262022.pdf",
      "cms_ira_insulin_vaccines_memo_2022.txt"),
]


def main():
    rows = ROWS + FORMULARY
    with open("route.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["product", "body", "decision", "date", "quote", "url", "capture"])
        w.writeheader()
        w.writerows(rows)
    # every quote must appear (whitespace-normalised, ellipses split) in its capture
    import re
    for r in rows:
        txt = open(r["capture"], encoding="utf-8", errors="replace").read()
        txt = re.sub(r"\s+", " ", re.sub(r"-\n\s*", "-", txt))  # rejoin hyphenated line breaks
        for part in r["quote"].split(" ... "):
            p = re.sub(r"\s+", " ", part.strip(" .")).strip()
            if p and not p.startswith("(") and p not in txt:
                print("QUOTE NOT FOUND:", r["product"], r["date"], "|", p[:80])
    print(len(rows), "rows written")


if __name__ == "__main__":
    main()
