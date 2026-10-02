"""Build route.csv from the captures in captures/, checking every quote is present verbatim
(whitespace-normalised) in the .txt version of its capture. Rows are written by hand from reading
the captured documents on 2026-10-02."""
import csv, re, os
BASE = os.path.dirname(os.path.abspath(__file__))
FK = "https://www.felleskatalogen.no/medisin/"
L = "https://legemiddelverket.no/Documents/Offentlig-finansiering-og-pris/Metodevurderinger/"
FEST = "https://www.dmp.no/globalassets/documents/om-oss/distribusjon-av-legemiddeldata/fest/festfiler/fest251.zip"
DMP26 = "https://www.dmp.no/globalassets/documents/offentlig-finansiering-og-pris/metodevurderinger/i/insulin_diabetes_2026_-endring-av-refusjonsvilkar.pdf"
NMG = "https://cg.optimizely.com/content/v2 (Optimizely Graph behind https://www.nyemetoder.no/metoder/)"
SIX = "https://www.sykehusinnkjop.no/492829/siteassets/avtaledokumenter/avtaler-legemidler/basislegemidler/alle-basis.xlsx"
HD1 = "https://www.helsedirektoratet.no/retningslinjer/diabetes/behandling-med-blodsukkersenkende-legemidler-ved-diabetes/insulinbehandling-og-behandlingsmal-ved-diabetes-type-1"
HD2 = "https://www.helsedirektoratet.no/retningslinjer/diabetes/behandling-med-blodsukkersenkende-legemidler-ved-diabetes/blodsukkersenkende-behandling-og-behandlingsmal-ved-diabetes-type-2"

R = []
def row(product, body, decision, date, quote, gloss, url, capture):
    R.append(dict(product=product, body=body, decision=decision, date=date,
                  quote=quote + (f" [{gloss}]" if gloss else ""), url=url, capture="captures/" + capture, _q=quote))

# ---- Tresiba
row("Tresiba (insulin degludec)", "Statens legemiddelverk (SLV)", "T1D: forhåndsgodkjent refusjon refused", "2015-04-28",
    "Insulin degludec (Tresiba) innvilges ikke forhåndsgodkjent refusjon ved diabetes type 1 etter folketrygdlovens § 5-14.",
    "not granted pre-approved reimbursement for type 1 diabetes", L+"T/Tresiba_Diabetes1_2015.pdf", "dmp_Tresiba_Diabetes1_2015.pdf")
row("Tresiba (insulin degludec)", "Statens legemiddelverk (SLV)", "T1D: §2 granted with vilkår 180 and 181; effective 2016-02-15", "2016-01-29",
    "er insulin degludec (Tresiba 100 E/ml) innvilget forhåndsgodkjent refusjon etter blåreseptforskriftens § 2",
    "granted pre-approved reimbursement under §2; conditions 180 (only after NPH fails owing to nocturnal hypoglycaemia or large glucose swings) and 181 (initiation by specialist)",
    L+"T/Tresiba_T1D_2016.pdf", "dmp_Tresiba_T1D_2016.pdf")
row("Tresiba (insulin degludec)", "Statens legemiddelverk (SLV)", "T2D: refusal upheld on renewed assessment (ICER about NOK 725,000/QALY vs NPH)", "2019-05-29",
    "vedtar at Tresiba ikke innvilges forhåndsgodkjent refusjon til behandling av diabetes type 2 basert på denne dokumentasjonen.",
    "decides Tresiba is not granted pre-approved reimbursement for type 2 diabetes on this documentation", L+"T/Tresiba_T2DM_2019.pdf", "dmp_Tresiba_T2DM_2019.pdf")
row("Tresiba (insulin degludec)", "DMP (FEST refusjonsdata)", "T2D codes T90/E11 on the §2 list from 2019-08-01 (granting document not located); vilkår 244 dated 2019-07-04",
    "2019-08-01",
    "<Refusjonskode V=\"T90\" S=\"2.16.578.1.12.4.1.1.7170\" DN=\"Diabetes type 2\" />\n            <GyldigFraDato>2019-08-01</GyldigFraDato>",
    "FEST refusjonsgruppe A10AE06_1: type 2 diabetes code valid from 2019-08-01", FEST, "fest251_a10a_refusjon_blocks.xml")
row("Tresiba (insulin degludec)", "Direktoratet for medisinske produkter (DMP)", "Vilkår 180, 181 and 244 removed; unconditional §2 for T1D and T2D; effective 2026-05-15", "2026-04-30",
    "Med hjemmel i legemiddelforskriften § 14-11 vedtar DMP å fjerne refusjonsvilkår 180, 181 og 244 for insulin degludek 100/200 E/ml (Tresiba) og insulin glargin 300 E/ml (Toujeo).",
    "DMP removes reimbursement conditions 180, 181 and 244 for degludec and glargine 300", DMP26, "dmp_insulin_diabetes_2026_endring-av-refusjonsvilkar.pdf")
row("Tresiba (insulin degludec)", "DMP (FEST refusjonsdata)", "Current refusjonsgruppe A10AE06_1: T89/E10/T90/E11, no vilkår attached (FEST file 2026-09-28)", "2026-09-28",
    "<RefusjonsberettighetBruk>Behandling av diabetes mellitus</RefusjonsberettighetBruk>",
    "reimbursable use: treatment of diabetes mellitus", FEST, "fest251_a10a_refusjon_blocks.xml")
row("Tresiba (insulin degludec)", "Felleskatalogen", "Packs listed as Blå resept; page still carries an 'Individuell stønad' box for T2D (page last changed 26.04.2024, so this predates the 2026 decision)", "2026-10-02",
    "Individuell stønad Insulin degludec Legemidler: Tresiba injeksjonsvæske Indikasjon: Diabetes mellitus type 2 .",
    "individual reimbursement: degludec, type 2 diabetes", FK+"tresiba-flextouch-tresiba-penfill-novo-nordisk-589607", "fk_tresiba.html")
# ---- Toujeo
row("Toujeo (insulin glargine 300 U/ml)", "Statens legemiddelverk (SLV)", "T1D: §2 granted with vilkår 180 and 181; price parity with Lantus; effective 2015-08-01", "2015-07-14",
    "er insulin glargin (Toujeo) innvilget forhåndsgodkjent refusjon etter blåreseptforskriftens § 2",
    "granted pre-approved reimbursement under §2 (type 1 diabetes, conditions 180 and 181)", L+"T/Toujeo_T1DM_2015.pdf", "dmp_Toujeo_T1DM_2015.pdf")
row("Toujeo (insulin glargine 300 U/ml)", "Statens legemiddelverk (SLV)", "T2D: general reimbursement refused", "2017-09-25",
    "Insulin glargin (Toujeo) innvilges ikke generell refusjon etter folketrygdlovens § 5-14.",
    "not granted general reimbursement", L+"T/Toujeo_T2D_2017.pdf", "dmp_Toujeo_T2D_2017.pdf")
row("Toujeo (insulin glargine 300 U/ml)", "DMP (FEST refusjonsdata)", "Refusjonsgruppe A10AE04_1 named 'Toujeo (med NPH-vilkår)'; T2D codes from 2019-08-01 (granting document not located); no vilkår attached in current file", "2019-08-01",
    "<GruppeNr V=\"A10AE04_1\" S=\"2.16.578.1.12.4.1.1.7451\" DN=\"Toujeo (med NPH-vilkår)\" />",
    "group label 'Toujeo (with NPH condition)'", FEST, "fest251_a10a_refusjon_blocks.xml")
row("Toujeo (insulin glargine 300 U/ml)", "Direktoratet for medisinske produkter (DMP)", "Vilkår 180, 181 and 244 removed; effective 2026-05-15", "2026-04-30",
    "Endringer medfører at aktuelle preparater har forhåndsgodkjent refusjon etter blåreseptforskriften § 2,",
    "the products now have pre-approved reimbursement under §2 (codes T89, T90, E10, E11, no conditions)", DMP26, "dmp_insulin_diabetes_2026_endring-av-refusjonsvilkar.pdf")
row("Toujeo (insulin glargine 300 U/ml)", "Sykehusinnkjøp HF (LIS)", "On national hospital basis-drug agreement (delkontrakt 28, Sanofi)", "2026-10-02",
    "135216 | Toujeo SoloStar inj 300 E/ml | 5x1,5 | MLPEN | 01 | C | K | 300E/ml | A10AE04 | Insulin glargin | 002345 | 28 |",
    "agreement row", SIX, "sykehusinnkjop_avtaleoversikt_basislegemidler.xlsx")
# ---- Fiasp
row("Fiasp (faster insulin aspart)", "Statens legemiddelverk (SLV)", "§2 granted, no vilkår; price capped at NovoRapid daily cost", "2017-05-19",
    "er insulin aspart (Fiasp) innvilget forhåndsgodkjent refusjon etter blåreseptforskriftens § 2",
    "granted pre-approved reimbursement under §2", L+"F/Fiasp_diabetes-type-1-og-2_2017.pdf", "dmp_Fiasp_diabetes-type-1-og-2_2017.pdf")
row("Fiasp (faster insulin aspart)", "Statens legemiddelverk (SLV)", "Conditions: none", "2017-05-19",
    "Vilkår: ingen", "conditions: none", L+"F/Fiasp_diabetes-type-1-og-2_2017.pdf", "dmp_Fiasp_diabetes-type-1-og-2_2017.pdf")
row("Fiasp (faster insulin aspart)", "Statens legemiddelverk (SLV)", "Reimbursement price tied to NovoRapid", "2017-05-19",
    "Refusjonsprisen settes slik at døgnkostnaden for insulin aspart (Fiasp) ikke skal være høyere enn maksimalpris/refusjonspris/trinnpris for referansealternativet (NovoRapid).",
    "daily cost may not exceed that of NovoRapid", L+"F/Fiasp_diabetes-type-1-og-2_2017.pdf", "dmp_Fiasp_diabetes-type-1-og-2_2017.pdf")
row("Fiasp (faster insulin aspart)", "Felleskatalogen", "Marketed; all four presentations Blå resept", "2026-10-02",
    "086515 Blå resept 343,00 C", "FlexTouch 5x3 ml, blue prescription, NOK 343.00", FK+"fiasp-fiasp-flextouch-fiasp-penfill-fiasp-pumpcart-novo-nordisk-640799", "fk_fiasp.html")
# ---- Lyumjev
row("Lyumjev (ultra-rapid lispro)", "Statens legemiddelverk (SLV)", "§2 granted, no vilkår (simplified assessment vs Humalog); effective 2021-02-15", "2021-01-25",
    "er insulin lispro (Lyumjev) innvilget forhåndsgodkjent refusjon etter blåreseptforskriftens §§ 2, jf. 1b",
    "granted pre-approved reimbursement under §2", L+"L/Lyumjev_DM_2021.pdf", "dmp_Lyumjev_DM_2021.pdf")
row("Lyumjev (ultra-rapid lispro)", "Statens legemiddelverk (SLV)", "Reimbursement price tied to Humalog", "2021-01-25",
    "Refusjonsprisen settes slik at døgnkostnaden for insulin lispro (Lyumjev) ikke skal være høyere enn maksimalpris/ refusjonspris/ trinnpris for referansealternativet, som i denne vurderingen er Humalog.",
    "daily cost may not exceed that of Humalog", L+"L/Lyumjev_DM_2021.pdf", "dmp_Lyumjev_DM_2021.pdf")
row("Lyumjev (ultra-rapid lispro)", "Felleskatalogen", "Marketed; vial, cartridge and KwikPen Blå resept", "2026-10-02",
    "391879 Blå resept 509,10 C", "KwikPen 5x3 ml, blue prescription, NOK 509.10", FK+"lyumjev-lilly-686975", "fk_lyumjev.html")
row("Lyumjev (ultra-rapid lispro)", "Sykehusinnkjøp HF (LIS)", "Vial and cartridge on hospital basis-drug agreement (delkontrakt 19, Lilly); KwikPen not listed", "2026-10-02",
    "553635 | Lyumjev inj 100 E/ml | 5x3 | MLSYL | 01 | C | K | 100E/ml | A10AB04 | Insulin lispro |  | 19 |",
    "agreement row", SIX, "sykehusinnkjop_avtaleoversikt_basislegemidler.xlsx")
# ---- rapid comparators
for prod, gid in [("NovoRapid (insulin aspart)", "A10AB05_1"), ("Humalog (insulin lispro)", "A10AB04_1")]:
    row(prod, "DMP (FEST refusjonsdata)", f"Refusjonsgruppe {gid}: codes T89/T90/W85/E10/E11/E13/E14/O24.4 from 2008, no vilkår", "2026-09-28",
        f"<GruppeNr V=\"{gid}\" S=\"2.16.578.1.12.4.1.1.7451\" DN=\"{gid}\" />", "rapid-acting analogue group, unconditional", FEST, "fest251_a10a_refusjon_blocks.xml")
# ---- glargine 100
row("Lantus (insulin glargine 100 U/ml)", "Statens legemiddelverk (SLV)", "T1D refusjonsrapport: cost-effective vs NPH (report signed 03-02-2008; DMP list year 2009)", "2008-02-03",
    "Legemiddelverket konkluderer ut fra dette med at insulin glargin er kostnadseffektivt sammenlilmet",
    "concludes glargine is cost-effective compared with NPH (OCR spelling as captured)", L+"L/Lantus_diabetes_type_I_2009.pdf", "dmp_Lantus_diabetes_type_I_2009.pdf")
row("Lantus (insulin glargine 100 U/ml)", "Statens legemiddelverk (SLV)", "T2D: refusal ('avslag' in filename); scanned PDF with no text layer, wording not quotable", "2012",
    "", "", L+"L/Lantus_diabtetes2_avslag_2012.pdf", "dmp_Lantus_diabetes2_avslag_2012.pdf")
row("Lantus/Abasaglar/Semglee (glargine 100 U/ml)", "Statens legemiddelverk (SLV)", "Vilkår 180 (T1D) and 244 (T2D) removed for glargine 100 with trinnpris; 181 retained for T1D", "2023-08-10",
    "Statens legemiddelverk vedtar å fjerne refusjonsvilkår for insulin glargin preparater med styrke 100 E/ml og med trinnpris.",
    "removes reimbursement conditions for glargine 100 U/ml products under stepped pricing", L+"I/Insulin-Glargin-100-E-ml_Diabetes_Fjerning-av-refusjonsvilkar_2023.pdf", "dmp_Insulin-Glargin-100_Fjerning-av-refusjonsvilkar_2023.pdf")
row("Lantus/Abasaglar/Semglee (glargine 100 U/ml)", "Direktoratet for medisinske produkter (DMP)", "Vilkår 181 removed; unconditional; effective 2026-05-15", "2026-04-30",
    "DMP fjerner også refusjonsvilkår 181 for insulin glargin 100/E (Abasaglar, Lantus og Semglee).",
    "DMP also removes condition 181 for glargine 100", DMP26, "dmp_insulin_diabetes_2026_endring-av-refusjonsvilkar.pdf")
row("Abasaglar and Semglee (glargine 100 U/ml biosimilars)", "Felleskatalogen", "Both listed as withdrawn products in 2025; neither appears in FEST 2026-09-28", "2025",
    "Abasaglar «Lilly» injeksjonsvæske (A10A E04 insulin glargin).", "Abasaglar listed under withdrawn medicines 2025 (Semglee listed on the same page)",
    "https://www.felleskatalogen.no/medisin/utgatte-preparater/2025", "fk_utgatte_preparater_2025.html")
row("Lantus (insulin glargine 100 U/ml)", "Sykehusinnkjøp HF (LIS)", "On hospital basis-drug agreement (delkontrakt 27, Sanofi)", "2026-10-02",
    "081996 | Lantus SoloStar inj 100E/ml | 5x3 | MLPEN | 01 | C | K | 100E/ml | A10AE04 | Insulin glargin | 002132 | 27 |",
    "agreement row", SIX, "sykehusinnkjop_avtaleoversikt_basislegemidler.xlsx")
# ---- Levemir
row("Levemir (insulin detemir)", "Statens legemiddelverk (SLV)", "T2D: general reimbursement refused", "2010-09-17",
    "Insulin detemir (Levemir) innvilges ikke generell refusjon etter folketrygdlovens § 5-14 for pasienter med diabetes type 2.",
    "not granted general reimbursement for type 2 diabetes", L+"L/Levemir_diabetes_type_II_2010.pdf", "dmp_Levemir_diabetes_type_II_2010.pdf")
row("Levemir (insulin detemir)", "DMP (FEST refusjonsdata)", "Group A10AE05_2 still carries vilkår 180+181 (T1D) and 244 (T2D); detemir was not in the 2026 decision", "2026-09-28",
    "Refusjon ytes kun til pasienter som til tross for optimal behandling med to daglige doser middels langtidsvirkende NPH-insulin har vedvarende utfordringer med hypoglykemier.",
    "vilkår 244: reimbursement only for people with persistent hypoglycaemia despite optimal twice-daily NPH", FEST, "fest251_a10a_vilkar.xml")
row("Levemir (insulin detemir)", "Felleskatalogen", "Penfill reimbursable until 31.03.2027 (product being withdrawn)", "2026-10-02",
    "Kan forskrives med refusjon til 31.03.2027", "can be prescribed with reimbursement until 31 March 2027", FK+"levemir-flexpen-levemir-penfill-novo-nordisk-560927", "fk_levemir.html")
# ---- system-level
row("All insulins named", "Nye Metoder", "No method ID for any of the insulins; full-text search of 1,347 methods returned 0 hits for degludek, glargin, aspart, lispro, detemir and all brand names (positive control pembrolizumab: 43)", "2026-10-02",
    "degludek: total=0", "search result", NMG, "nyemetoder_graph_search_2026-10-02.txt")
row("All insulins named", "Nye Metoder", "Scope: Beslutningsforum decides for the specialist health service; blue-prescription insulins are assessed by DMP under the folketrygd instead",
    "2026-10-02",
    "Beslutningsforum for nye metoder (Beslutningsforum) beslutter om en metode kan tas i bruk eller ikke i spesialisthelsetjenesten.",
    "the decision forum decides whether a method may be used in the specialist health service", "https://www.nyemetoder.no/innforing-av-nye-metoder/beslutning/", "nyemetoder_beslutning.html")
row("All insulins named", "DMP", "DMP list of completed assessments classes every insulin report as financed by Folketrygd (not Sykehus)", "2026-10-02",
    "Lyumjev | insulin lispro | Diabetes mellitus |  | https://legemiddelverket.no/Documents/Offentlig-finansiering-og-pris/Metodevurderinger/L/Lyumjev_DM_2021.pdf | 2021 | Folketrygd | N/A", "Lyumjev row: financed by the National Insurance scheme, no Nye Metoder ID (same pattern for every insulin row)", "https://www.dmp.no/offentlig-finansiering/metodevurdering-av-medisinske-produkter/metodevurdering-av-legemidler/fullforte-metodevurderinger-for-legemidler",
    "dmp_fullforte_metodevurderinger_legemidler.html")
row("All insulins named", "Sykehusinnkjøp HF (LIS)", "No LIS recommendation page for insulin found; hospital basis agreement lists Lilly and Sanofi insulins only, no Novo Nordisk product", "2026-10-02",
    "insulin: total=6", "site search hits (pumps, CGM and the basis-drug list)", "https://cg.optimizely.com/content/v2 (sykehusinnkjop.no content)", "sykehusinnkjop_graph_search_2026-10-02.txt")
row("Basal insulin (T1D)", "Helsedirektoratet", "Nasjonal faglig retningslinje: 'Oppstart og valg av insulin ved diabetes type 1', strong recommendation, last professional change 14 September 2016", "2016-09-14",
    "Standard insulinbehandling ved diabetes type 1 er en kombinasjon av langtidsvirkende insulinanalog eller NPH-insulin og hurtigvirkende insulinanalog.",
    "standard treatment in type 1 is a long-acting analogue or NPH plus a rapid-acting analogue", HD1, "hdir_diabetes_insulinbehandling_type1.html")
row("Basal insulin (T1D)", "Helsedirektoratet", "Practical text under the same recommendation: no updated health-economic case for analogues for everyone; rapid analogue preferred at meals", "2016-09-14",
    "Per i dag foreligger ikke en oppdatert helseøkonomisk vurdering som understøtter bruk av langtidsvirkende insulinanalog til alle pasienter med diabetes type 1.",
    "there is currently no updated health-economic assessment supporting long-acting analogues for all people with type 1", HD1, "hdir_diabetes_insulinbehandling_type1.html")
row("Rapid-acting insulin (T1D)", "Helsedirektoratet", "Meal-time insulin preference", "2016-09-14",
    "Som måltidsinsulin foretrekkes hurtigvirkende insulinanalog.", "a rapid-acting analogue is preferred as meal-time insulin; no mention of Fiasp or Lyumjev", HD1, "hdir_diabetes_insulinbehandling_type1.html")
row("Basal insulin (T2D)", "Helsedirektoratet", "'Valg av blodsukkersenkende legemiddel etter metformin', weak recommendation, last professional change 12 September 2018", "2018-09-12",
    "*De fleste pasienter kan behandles med NPH-insulin. Utvalgte pasienter vil ha nytte av langtidsvirkende insulinanalog (glargin, glargin-300, detemir, degludec), særlig ved nattlig hypoglykemi eller åpenbart for kort virketid av NPH-insulin.",
    "most people can use NPH; selected people benefit from a long-acting analogue, particularly with nocturnal hypoglycaemia or too-short NPH action", HD2, "hdir_diabetes_blodsukkersenkende_type2.html")

# verify quotes against .txt captures (whitespace-normalised)
def norm(s): return re.sub(r"\s+", " ", s).strip()
bad = 0
for r in R:
    if not r["_q"]: continue
    cap = os.path.join(BASE, r["capture"])
    txt = cap.rsplit(".", 1)[0] + ".txt"
    t = norm(open(txt, encoding="utf-8", errors="replace").read())
    if norm(r["_q"]) not in t:
        bad += 1; print("NOT FOUND:", r["product"], r["date"], r["_q"][:80], "in", txt)
    if not os.path.exists(cap): print("MISSING CAPTURE", cap)
print("rows", len(R), "unverified", bad)
with open(os.path.join(BASE, "route.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["product", "body", "decision", "date", "quote", "url", "capture"], extrasaction="ignore")
    w.writeheader(); w.writerows(R)
