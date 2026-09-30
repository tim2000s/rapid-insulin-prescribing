"""Write formulary_positions_devolved.csv and access_log.csv from the entries read on 30 September 2026.

Every wording field below is quoted from a page or document saved under raw/. The coding
rule, applied to the less restrictive of Fiasp and Lyumjev:
  open: listed, no clinical criteria and no specialist requirement;
  specialist: specialist initiation or recommendation, or clinical criteria, without a
    requirement that a standard analogue has failed first;
  second_line_or_excluded: prior failure of a standard analogue required, pregnancy only,
    not listed, or not approved.
"""
import csv

READ_ON = "2026-09-30"
WOS = "https://formulary.nhs.scot/west/endocrine-system/diabetes-mellitus/diabetes-mellitus-type-1/"
ERF = "https://formulary.nhs.scot/east/endocrine-system/diabetes-mellitus/diabetes-mellitus-type-1/"
GRAMP = "https://www.grampianformulary.scot.nhs.uk/chaptersSubDetails.asp?FormularySectionID=6&SubSectionRef=06.01&SubSectionID=A100"
HIGH = ("https://www.rightdecisions.scot.nhs.uk/tam-treatments-and-medicines-nhs-highland/formularies/highland-formulary/"
        "endocrine-system-formulary/diabetes-formulary-endocrine/insulins-formulary-endocrine/rapid-acting-insulins-formulary-endocrine/"
        "recombinant-human-insulin-analogues-formulary-endocrine/")
INFORM = "https://formulary.wales.nhs.uk/indexNew.aspx?prefixUrl="

WOS_FIASP = ('Third choice recommendation(s), flag "Specialist Recommendation: may be initiated in primary care on the recommendation of a consultant or '
             'specialist practitioner working with a multidisciplinary team." Text: "Insulin aspart (Fiasp) has a faster onset of action than NovoRapid and may be '
             'useful in patients failing to achieve glycaemic control with current fast acting insulin." (vials, Penfill)')
WOS_LYU = ('Third choice recommendation(s), same Specialist Recommendation flag. Text: "Insulin lispro (Lyumjev) has a faster onset of action than Humalog." '
           '(vials, cartridges, KwikPen, Junior KwikPen)')
WOS_FIRST = ('First choice: "Insulin aspart (Trurapi)."; second choice: "Insulin aspart (NovoRapid)."; third choice: Humalog, Fiasp, Lyumjev. '
             'All carry the Specialist Recommendation flag.')
WOS_REASON = ('Both carry the Specialist Recommendation flag, which every rapid-acting analogue including first-choice Trurapi also carries; Fiasp text "may be useful in patients '
              'failing to achieve glycaemic control" is descriptive, not a stated requirement; no failure criterion for Lyumjev.')

ERF_FIASP = ('Second choice recommendation(s), "[Specialist Initiation: may be continued in a primary care setting]". Text: "Insulin aspart (Fiasp) has a faster onset of action '
             'than NovoRapid and care should be taken when prescribing." Prescribing note: "may be useful in patients failing to achieve glycaemic control with current fast acting insulin."')
ERF_LYU = ('Third choice recommendation(s), "[Specialist Initiation: may be continued in a primary care setting]". Text: "Insulin lispro (Lyumjev) has a faster onset of action than '
           'Humalog and care should be taken when prescribing." Same prescribing note as Fiasp.')
ERF_FIRST = ('First choice: "Insulin aspart (Trurapi or NovoRapid)."; second choice: Humalog, Apidra, Fiasp; third choice: Lyumjev. All flagged Specialist Initiation.')
ERF_REASON = ('Fiasp is second choice with Specialist Initiation, the same flag as first-choice Trurapi/NovoRapid; "may be useful in patients failing..." is a prescribing note, '
              'not a stated requirement.')

GRAMP_FIASP = ('"Restricted", traffic light "Amber 1" (key: "Available for restricted use under specialist supervision. Treatment may be initiated in Primary Care on the '
               'recommendation of a consultant/specialist."), restricted item: "Considered for selected patients, e.g. those on insulin pumps". Vial, cartridge. '
               'Fiasp FlexTouch listed under Non Formulary Items.')
GRAMP_FIRST = ('Apidra, Humalog 100 units/mL, NovoRapid each "Formulary" (no traffic light shown, no ranking). Trurapi not listed.')

rows = [
    # ---------------- Scotland: West of Scotland Formulary (current) ----------------
    *[dict(nation="Scotland", area=f"{b} (West of Scotland Formulary, current)", fiasp_position=WOS_FIASP, lyumjev_position=WOS_LYU,
           first_line_rapid=WOS_FIRST, biosimilar_first_line="yes (Trurapi first choice)", restriction_class="specialist",
           coding_reason=WOS_REASON, source_url=WOS, entry_date="30/07/2026 (history note: \"Regional formulary chapter launched.\")", read_on=READ_ON)
      for b in ["Greater Glasgow and Clyde", "Lanarkshire", "Ayrshire and Arran", "Forth Valley", "Dumfries and Galloway"]],
    # ---------------- Scotland: West board predecessors ----------------
    dict(nation="Scotland", area="Greater Glasgow and Clyde (GGC Adult Formulary before WoS; archived copy)",
         fiasp_position=('Fiasp not named. Preferred List entry "INSULIN ASPART": "Restrictions: Restricted to initiation by clinicians, either in primary care or the acute setting, '
                         'experienced in the treatment of diabetes." Prescribing note: "Insulin aspart preparations may differ in terms of speed of onset of action and should therefore be prescribed by brand name."'),
         lyumjev_position=('Not named. Preferred List entry "INSULIN LISPRO (HUMALOG) (injection)" with the same restriction; note: "Currently, only the 100 units/ml preparations have '
                           'been considered and added to Formulary. Other strengths are currently non-Formulary"'),
         first_line_rapid='Preferred List: INSULIN ASPART (brand not stated), INSULIN LISPRO (HUMALOG), SOLUBLE INSULIN. Total Formulary: INSULIN GLULISINE (APIDRA).',
         biosimilar_first_line="not named (aspart listed by molecule)",
         restriction_class="specialist",
         coding_reason=('Fiasp is covered only through the molecule-level aspart entry, whose restriction to clinicians experienced in diabetes (primary or acute care) applies '
                        'equally to NovoRapid; coded specialist on that restriction, and it would read open if experienced-clinician wording is not treated as a specialist requirement.'),
         source_url="https://web.archive.org/web/20251210174023/https://ggcmedicines.org.uk/formulary/endocrine-system-6/drugs-used-in-diabetes/",
         entry_date="undated page; Wayback capture 10/12/2025; live URL now returns 404", read_on=READ_ON),
    dict(nation="Scotland", area="Lanarkshire (NHSL Joint Adult Formulary before WoS)",
         fiasp_position="Not read: insulins page is password protected (\"Please enter the related password for this item in order to view this content.\")",
         lyumjev_position="Not read (same page)", first_line_rapid="Not read", biosimilar_first_line="not read",
         restriction_class="not_coded", coding_reason="Predecessor entry inaccessible; no Wayback capture of the insulins page was found.",
         source_url="https://www.rightdecisions.scot.nhs.uk/nhsl-medicines-guidance/joint-adult-formulary/chapter-6-endocrine-system/drugs-used-in-diabetes/insulins/",
         entry_date="n/a", read_on=READ_ON),
    dict(nation="Scotland", area="Ayrshire and Arran (Abbreviated Adult Joint Formulary, May 2026, before WoS endocrine chapter)",
         fiasp_position=('"S Insulin aspart 100 units/mL solution for injection (Fiasp®)" under Short acting insulins (S = "Specialist initiation"); section note: "Insulin should be '
                         'initiated on specialist advice only." and "Insulin preparations currently under review, and so the following is not a complete list"'),
         lyumjev_position="Not listed",
         first_line_rapid='No ranking: "S soluble insulin (Actrapid®)", "S Insulin aspart (Fiasp®)", "S insulin aspart (NovoRapid®)", "S insulin (Humalog®)".',
         biosimilar_first_line="no (no biosimilar rapid-acting listed)",
         restriction_class="specialist",
         coding_reason='Fiasp carries S (specialist initiation), the same symbol as NovoRapid and Humalog; no clinical criteria stated; Lyumjev not listed.',
         source_url="https://www.nhsaaa.net/wp-content/uploads/NHSAAAbbreviatedformulary.pdf",
         entry_date="May 2026 (document header; PDF created 08/06/2026)", read_on=READ_ON),
    dict(nation="Scotland", area="Forth Valley (Forth Valley Formulary before WoS; archived copy)",
         fiasp_position=('Not named. Class entry "Insulin" with comment: "For all insulins recommendation by practitioner experienced in the management of diabetes"'),
         lyumjev_position="Not named (same class entry)",
         first_line_rapid="No products named; single class entry \"Insulin\".", biosimilar_first_line="not named",
         restriction_class="specialist",
         coding_reason=('Class-wide requirement for recommendation by a practitioner experienced in diabetes; coded specialist on that wording, which applies to every insulin; '
                        'this is a December 2022 version and later pre-WoS versions were not found.'),
         source_url="https://web.archive.org/web/20230402014112/https://pharmacies.nhsforthvalley.com/wp-content/uploads/sites/6/2019/03/BNF6-Endocrine.pdf",
         entry_date='"Forth Valley Formulary Last amended December 22" (Wayback capture 02/04/2023)', read_on=READ_ON),
    dict(nation="Scotland", area="Dumfries and Galloway (Joint Formulary 2025, before WoS)",
         fiasp_position=('"Ultra short acting insulin": "Fiasp ®Penfill catrridge 3ml▼", "Fiasp ®FlexTouch pre-filled pen▼", "Fiasp ® vial 10ml▼"; section note: '
                         '"Insulin should be initiated on specialist advice only"'),
         lyumjev_position="Not listed",
         first_line_rapid='No ranking. Short acting insulins: Humalog, "Admelog Sanofi®" (biosimilar lispro), Novorapid, Humulin S, Apidra.',
         biosimilar_first_line="no ranking; Admelog listed, Trurapi not listed",
         restriction_class="specialist",
         coding_reason='Fiasp listed without clinical criteria but under the section rule "Insulin should be initiated on specialist advice only", which covers all insulins.',
         source_url="https://www.communitypharmacy.scot.nhs.uk/nhs-dumfries-galloway/wp-content/uploads/sites/5/2025-D-and-G-Formulary.pdf",
         entry_date="2025 (document title)", read_on=READ_ON),
    # ---------------- Scotland: East Region Formulary ----------------
    *[dict(nation="Scotland", area=f"{b} (East Region Formulary)", fiasp_position=ERF_FIASP, lyumjev_position=ERF_LYU, first_line_rapid=ERF_FIRST,
           biosimilar_first_line="yes, jointly (\"Trurapi or NovoRapid\" first choice)", restriction_class="specialist", coding_reason=ERF_REASON,
           source_url=ERF, entry_date="latest history note 26/02/2026 (\"Prescribing information updated, ERWG Oct 25\"); Trurapi added 21/08/2024", read_on=READ_ON)
      for b in ["Lothian", "Fife", "Borders"]],
    # ---------------- Scotland: Tayside ----------------
    dict(nation="Scotland", area="Tayside (Tayside Area Formulary via Tayside Diabetes MCN Handbook)",
         fiasp_position=('MCN Handbook "Treatment with Insulin": "Fiasp (vial, cartridge)", Type 1 column: "2nd line bolus insulin for those who require a faster onset of action". '
                         'Tayside Area Formulary 06.01.01: "Insulin preparations recommended within Tayside are in the Tayside Diabetes MCN Handbook"'),
         lyumjev_position="Not listed in the MCN Handbook table; Tayside Area Formulary search for \"lyumjev\" found 0 matches",
         first_line_rapid='"Trurapi (vial, cartridge, SoloStar pen)" "1st line bolus insulin"; Humalog and Apidra listed without a line; NovoRapid not listed.',
         biosimilar_first_line="yes (Trurapi 1st line bolus)",
         restriction_class="specialist",
         coding_reason=('Fiasp has a clinical criterion ("for those who require a faster onset of action") and is labelled "2nd line", but no failure of a standard analogue is stated; '
                        'borderline, and it reads as second_line_or_excluded if "2nd line" is taken to require prior use of the first-line insulin. No specialist requirement stated.'),
         source_url=("https://www.taysideformulary.scot.nhs.uk/chaptersSubDetails.asp?FormularySectionID=6&SubSectionRef=06.01&SubSectionID=A100 ; "
                     "https://www.nhstaysidecdn.scot.nhs.uk/NHSTaysideWeb/idcplg?IdcService=GET_SECURE_FILE&Rendition=web&RevisionSelectionMethod=LatestReleased&noSaveAs=1&dDocName=prod_392780"),
         entry_date='MCN Handbook "Last updated May 2026"', read_on=READ_ON),
    # ---------------- Scotland: Grampian, Orkney, Shetland ----------------
    *[dict(nation="Scotland", area=a, fiasp_position=GRAMP_FIASP,
           lyumjev_position='Not listed ("Looking for lyumjev found 0 matches"); the "Ultra-rapid insulin analogues" subheading has no entries',
           first_line_rapid=GRAMP_FIRST, biosimilar_first_line="no (Trurapi not listed)", restriction_class="specialist",
           coding_reason=('Fiasp is Amber 1 (initiation on consultant/specialist recommendation) and "Considered for selected patients, e.g. those on insulin pumps"; '
                          'pumps are an example, not the only use; no failure criterion; Lyumjev not listed.'),
           source_url=GRAMP + (" ; " + extra if extra else ""), entry_date="undated entry; latest Fiasp amendment 12/02/2026 (\"Fiasp® FlexTouch® discontinued; FG meeting 20/01/2026\")",
           read_on=READ_ON)
      for a, extra in [("Grampian (Grampian Area Formulary)", ""),
                       ("Orkney (uses Grampian Area Formulary)", "https://www.ohb.scot.nhs.uk/our-services/pharmacy-and-prescribing/ lists \"NHS Grampian Formulary\" under useful websites"),
                       ("Shetland (uses Grampian Area Formulary)", "https://www.nhsshetland.scot/us/pharmacy-prescribing: \"those available are those within the Grampian Formulary\"")]],
    # ---------------- Scotland: Highland, Western Isles ----------------
    *[dict(nation="Scotland", area=a,
           fiasp_position=('Listed under INSULIN ASPART: "10mL vial (Fiasp®, NovoRapid®)", "3mL cartridge (Fiasp Penfill®, NovoRapid Penfill®)", "3 mL pre-filled pen (Fiasp Flextouch®, ...)". '
                           'Dosage: "As per SMC 1227/17: treatment of diabetes mellitus in adults." No restriction text.'),
           lyumjev_position=('Listed under INSULIN LISPRO: "10mL vial (Humalog®, Lyumjev®)", "3mL cartridge (Humalog®, Lyumjev®)", pre-filled pens incl. Lyumjev KwikPen, Lyumjev Junior Kwikpen '
                             '(added 08/07/26), Lyumjev KwikPen 200 units/ml. No restriction text.'),
           first_line_rapid="No ranking; insulin aspart (Fiasp, NovoRapid), glulisine (Apidra), lispro (Humalog, Lyumjev).",
           biosimilar_first_line="no (Trurapi not listed)", restriction_class="open",
           coding_reason=('Both listed with no clinical criteria and no specialist flag; the parent Insulins page says only "Insulin preparations should be initiated by appropriately '
                          'trained individuals", which applies to all insulins and is not a specialist requirement.'),
           source_url=HIGH + (" ; " + extra if extra else ""), entry_date="v1.2 08/07/26; \"Last reviewed: 19/01/2023\"", read_on=READ_ON)
      for a, extra in [("Highland (Highland Formulary, TAM)", ""),
                       ("Western Isles (uses Highland Formulary)", "https://www.wihb.scot.nhs.uk/our-services/pharmacy-services/primary-care-pharmacy/ links \"Medicines Formulary Page\" to the NHS Highland TAM formularies")]],
    # ---------------- Wales ----------------
    dict(nation="Wales", area="Aneurin Bevan",
         fiasp_position=('"G - Green". "Fiasp® was suitable for initiation by non-specialist prescribers (designated Green in the local Traffic Light system), this was consistent with the '
                         'current advice for NovoRapid®." "(MTC July 2017)"'),
         lyumjev_position='Listed in "Insulin lispro ( Humalog )" entry, "G - Green", Lyumjev vials, cartridges, KwikPen 100 and 200; no criteria.',
         first_line_rapid='No ranking; NovoRapid entry "G - Green": "Trurapi- Biosimilar insulin aspart is also approved for use within ABUHB".',
         biosimilar_first_line="no (Trurapi \"also approved\")", restriction_class="open",
         coding_reason='Fiasp Green and explicitly "suitable for initiation by non-specialist prescribers"; Lyumjev Green with no criteria.',
         source_url=INFORM + "abbformulary", entry_date="Fiasp date added 27-11-2023; lispro entry 02-11-2018", read_on=READ_ON),
    dict(nation="Wales", area="Betsi Cadwaladr",
         fiasp_position=('Insulin aspart entry "G - Green"; "Fiasp - For specialist initiation in adult patients with type 1 diabetes mellitus or gestational diabetes. (DTG 09/18). [AmberI]" '
                         'and "Fiasp - Treatment of diabetes mellitus in adolescents and children aged 1 year and above. (DTG 08/20) [AmberI]"'),
         lyumjev_position=('"Lyumjev® In adults with type 1 diabetes, as a second-line choice, where patients have failed to achieve adequate control with standard short/long acting insulin '
                           'combinations DTG 12/20"'),
         first_line_rapid="No ranking; insulin aspart entry lists NovoRapid, Trurapi, Fiasp; insulin lispro entry Humalog, Lyumjev.",
         biosimilar_first_line="no ranking (Trurapi listed)", restriction_class="specialist",
         coding_reason='Fiasp is AmberI "For specialist initiation" in type 1 or gestational diabetes (clinical criteria, no failure requirement); Lyumjev requires prior failure but is the more restrictive.',
         source_url=INFORM + "bcuformulary", entry_date="entry date added 29-12-2016; Fiasp DTG 09/18 and 08/20; Lyumjev DTG 12/20", read_on=READ_ON),
    dict(nation="Wales", area="Cardiff and Vale",
         fiasp_position='"S - Specialist initiated". "Fiasp - Faster Acting Insulin Aspart is Specialist Inititated for the treatment of Type 1 diabetes mellitus."',
         lyumjev_position="Not listed (search for \"lyumjev\" returned no results; insulin lispro entries list Humalog only)",
         first_line_rapid='"insulin aspart (Trurapi - 1st choice)", "R - Specialist recommended"; NovoRapid and Humalog "R - Specialist recommended".',
         biosimilar_first_line="yes (Trurapi 1st choice)", restriction_class="specialist",
         coding_reason='Fiasp specialist initiated, type 1 diabetes; no failure requirement; Lyumjev not listed.',
         source_url=INFORM + "cavformulary", entry_date="Fiasp: \"no date recorded\"; Trurapi added 19-12-2025", read_on=READ_ON),
    dict(nation="Wales", area="Cwm Taf Morgannwg",
         fiasp_position=('"S 1st - Specialist initiated 1st Line". "It is an option to improve control of post-prandial hyperglycaemia, particularly where the timing of the injection relative to '
                         'meal is restricted ... This includes pregnancy and insulin pump use where necessary."'),
         lyumjev_position='Lyumjev 100 and 200: "S 1st - Specialist initiated 1st Line"; mealtime dosing text only, no criteria.',
         first_line_rapid='All "S 1st - Specialist initiated 1st Line": Trurapi, NovoRapid, Humalog 100, Fiasp, Lyumjev.',
         biosimilar_first_line="yes, jointly (Trurapi 1st line alongside originators and ultra-rapids)", restriction_class="specialist",
         coding_reason='Lyumjev is 1st line with no clinical criteria but specialist initiated, the same status as NovoRapid, Humalog and Trurapi.',
         source_url=INFORM + "cttformulary", entry_date="Fiasp 25-10-2017; Lyumjev 24-03-2021; Trurapi 06-06-2025", read_on=READ_ON),
    dict(nation="Wales", area="Hywel Dda",
         fiasp_position=('"S - Specialist initiated". "Following submission of an evaluation of use by the Specialist Diabetic Team FIASP has been reclassifed. JP March 2019". '
                         'Earlier note retained: "Fiasp ® is approved for a limited number ( type I diabetes with persistent post prandial hyperglycaemia ) ... JP July 2017"'),
         lyumjev_position='"S - Specialist initiated" (Humalog, Lyumjev entry). "Lyumjev Available as a cost-effective alternative to FIASP in selected patients. Specialist Initiated as per licensed indications. [MMSC Sept 2020; SEB 4th November 2020]"',
         first_line_rapid=('"Insulin aspart Trurapi/Novorapid" "S - Specialist initiated" ("please note that this includes GPs who initiate insulin"); quotes NICE "use the product with the lowest '
                           'acquisition cost"; NovoRapid FlexPen to Trurapi SoloStar switch from September 2024.'),
         biosimilar_first_line="not ranked; lowest-acquisition-cost wording and Trurapi switch", restriction_class="specialist",
         coding_reason='Lyumjev specialist initiated "in selected patients" within licence; Fiasp specialist initiated after 2019 reclassification; no failure requirement.',
         source_url=INFORM + "hddformulary", entry_date="Fiasp 02-08-2017 (reclassified March 2019); Lyumjev MMSC Sept 2020; Trurapi entry 10-07-2024", read_on=READ_ON),
    dict(nation="Wales", area="Powys",
         fiasp_position=('Within "Insulin Aspart" entry: "GREEN - First line medicines which may be freely prescribed by all prescribers within local or national recommendations." '
                         'Fiasp vials and Penfill listed alongside NovoRapid and Trurapi; no criteria.'),
         lyumjev_position=('"BLUE - Second line medicines - to be initiated and prescribed by diabetic nurse team." "For patients with type 1 and type 2 diabetes including patients using insulin '
                           'pumps who have significant post-prandial hyperglycaemia (>10 mmol/L at 2 hours) despite optimised use of conventional rapid acting insulin analogues such as Humalog"'),
         first_line_rapid='Insulin aspart entry GREEN covering Fiasp, NovoRapid, Trurapi; Humalog "GREEN*".',
         biosimilar_first_line="no ranking (Trurapi in GREEN aspart entry)", restriction_class="open",
         coding_reason='Fiasp sits in the GREEN aspart entry with no criteria; Lyumjev requires prior optimised conventional analogue but is the more restrictive.',
         source_url=INFORM + "powformulary", entry_date="\"no date recorded\"", read_on=READ_ON),
    dict(nation="Wales", area="Swansea Bay",
         fiasp_position=('"S - Specialist initiated". "Specialist initiation only." "Approved for use in SBUHB in children and young people with type 1 DM in accordance with NICE NG18"'),
         lyumjev_position=('Insulin Lispro entry "2 nd - Second line including GP use"; "Lyumjev (insulin lispro) has been accepted on SBUHB formulary as an ultra-rapid acting insulin lispro '
                           'formulation. For specialist initiation/recommendation by diabetes services." Lyumjev presentations marked S.'),
         first_line_rapid='Insulin aspart (NovoRapid, Trurapi) and lispro (Humalog) "2 nd - Second line including GP use"; "insulin analogues are second line formulary choices after human insulin products".',
         biosimilar_first_line="no ranking (Trurapi listed with NovoRapid)", restriction_class="specialist",
         coding_reason='Lyumjev for specialist initiation/recommendation with no failure criterion ("second line" refers to analogues after human insulin); Fiasp specialist only.',
         source_url=INFORM + "abmformulary", entry_date="Fiasp 16-07-2018; lispro entry \"no date recorded\"", read_on=READ_ON),
    # ---------------- Northern Ireland ----------------
    dict(nation="Northern Ireland", area="Northern Ireland Formulary (regional)",
         fiasp_position=('"Fiasp ®" listed in the "Rapid (analogue)" column of "Formulary choices" (with Apidra, Humalog 100, Humalog 200, NovoRapid); no restriction text. '
                         'General advice: "Insulin should only be initiated and managed by healthcare professionals with the relevant expertise and training."'),
         lyumjev_position="Not listed (not in 6.1.1 table; site search for \"lyumjev\" returned no results)",
         first_line_rapid='"Rapid (analogue)": Apidra, Humalog 100, Humalog 200, NovoRapid, Fiasp; "The table below indicates preferred choices where all things are equal regarding device choice." No order stated.',
         biosimilar_first_line="no (Trurapi not listed)", restriction_class="open",
         coding_reason='Fiasp is a formulary choice with no criteria or specialist flag; the expertise sentence is general advice for all insulins; Lyumjev not listed.',
         source_url="https://niformulary.hscni.net/formulary/6-0-endocrine/6-1-drugs-used-in-diabetes/6-1-1-insulins/",
         entry_date="page undated; WordPress API modified 2026-05-01", read_on=READ_ON),
]

cols = ["nation", "area", "fiasp_position", "lyumjev_position", "first_line_rapid", "biosimilar_first_line",
        "restriction_class", "coding_reason", "source_url", "entry_date", "read_on"]
with open("formulary_positions_devolved.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

national = [
    ["Scotland", "SMC advice, Fiasp", "https://scottishmedicines.org.uk/medicines-advice/insulin-aspart-fiasp-abbreviatedsubmission-122717/",
     "read", "SMC 1227/17, abbreviated submission, \"insulin aspart (Fiasp®) is accepted for use within NHS Scotland.\" Indication: adults. Advice dated 10 March 2017, published 10 April 2017. Saved raw/smc_fiasp_122717*.html/.pdf"],
    ["Scotland", "SMC advice, Lyumjev", "https://scottishmedicines.org.uk/search/?keywords=lyumjev",
     "no record found", "SMC site search: \"Your search for \"lyumjev\" produced 0 results\"; search for \"insulin lispro\" and a paged search for \"insulin\" list only Humalog KwikPen (508/08) and Humalog Mix (509/08)."],
    ["Scotland", "Scottish Diabetes Group guidance", "https://www.diabetesinscotland.org.uk/?s=insulin",
     "not found", "Site search returned \"No Results Found\" for insulin, biosimilar and fiasp; the search appears non-functional. Web searches found no national rapid-acting or biosimilar insulin guidance."],
    ["Scotland", "Medicine Supply Alert Notices", "https://www.publications.scot.nhs.uk/files/msan-2024-05.pdf ; https://www.publications.scot.nhs.uk/files/msan-2025-53.pdf ; https://www.publications.scot.nhs.uk/files/msan-2024-23.pdf",
     "read", "MSAN(2024)05, 6 March 2024: Fiasp FlexTouch out of stock April 2024 to January 2025. MSAN headed \"(2024) 53\", dated 16 December 2025: Fiasp FlexTouch discontinued. MSAN(2024)23, 13 May 2024: Humalog vials; names Trurapi or NovoRapid vials for adult pump users."],
    ["Wales", "AWMSG, Fiasp", "https://awttc.nhs.wales/accessing-medicines/medicine-recommendations/insulin-aspart-fiasp/",
     "read", "\"Medicine does not meet criteria for AWMSG assessment\"; \"Excluded from appraisal by AWMSG as meets exclusion criteria 6.\" Reference 2787, issued 30/11/2016."],
    ["Wales", "AWMSG, Lyumjev", "https://awttc.nhs.wales/accessing-medicines/medicine-recommendations/insulin-lispro-liumjev/",
     "read", "Listed as \"insulin lispro (Liumjev®)\", 100 and 200 units/ml; \"Excluded from appraisal by AWMSG as meets exclusion criteria 6.\" Reference 3703, issued 22/04/2020."],
    ["Wales", "AWMSG, Trurapi", "https://awttc.nhs.wales/accessing-medicines/medicine-recommendations/insulin-aspart-sanofi-trurapi/",
     "read", "\"Excluded from appraisal by AWMSG as meets exclusion criterion 11.\" Reference 4858, issued 17/02/2021."],
    ["Wales", "AWMSG exclusion criteria document", "https://awttc.nhs.wales/files/pre-2025-appraisal-process-documents-archive/awmsg-exclusion-criteria-pdf-430kb1/",
     "not read", "Linked PDF opens in a script-rendered viewer; the fetched page body was a 404 page and WebFetch reported the same. Text of criteria 6 and 11 not obtained."],
    ["Wales", "All Wales insulin or biosimilar guidance", "https://awttc.nhs.wales/files/national-prescribing-indicators/national-prescribing-indicators-2025-2026-specifications-pdf/",
     "read", "NPI 2025-2026 \"Best value biological medicines\" basket lists infliximab, etanercept, rituximab, trastuzumab, adalimumab, ranibizumab, ustekinumab; no insulin. No All Wales rapid-acting insulin guidance found."],
    ["Wales", "InForm formulary portal", "https://formulary.wales.nhs.uk/",
     "read", "ASP.NET postback site with no per-entry URLs; entries reached by replaying the search postback (inform_fetch.py, inform_sweep.py). Board prefixes: abb, bcu, cav, ctt, hdd, pow, abm (+formulary)."],
    ["Northern Ireland", "Managed Entry, Fiasp", "https://niformulary.hscni.net/managed-entry/managed-entry-decisions/",
     "read", "Table is script-loaded; rows pulled from the site's WP Table Manager endpoint (table 1111). \"In Northern Ireland, insulin aspart (Fiasp®) is accepted for use for the treatment of diabetes mellitus in adults.\" Status Accepted, added 08/05/2017, guidance link SMC. No Lyumjev row among 1,082 rows."],
    ["Northern Ireland", "Managed Entry of Biosimilars", "https://niformulary.hscni.net/managed-entry/biosimilars/",
     "read", "\"where the originator product has been accepted for use in Northern Ireland, any biosimilar medicine will generally also be deemed 'accepted for use'\"; example given is Abasaglar; \"Biosimilar medicines should always be prescribed by brand name.\" Page modified 2026-06-04 (WordPress API)."],
    ["Northern Ireland", "DoH / SPPG biosimilar insulin guidance", "https://online.hscni.net/?s=insulin",
     "not found", "SPPG site search for insulin lists a \"Choice of insulin glargine\" file and needle and pump documents; search for biosimilar returned no links; no rapid-acting or biosimilar aspart guidance found."],
    ["Scotland", "Lanarkshire predecessor formulary", "https://www.rightdecisions.scot.nhs.uk/nhsl-medicines-guidance/joint-adult-formulary/chapter-6-endocrine-system/drugs-used-in-diabetes/insulins/",
     "not read", "Password-protected page; Wayback CDX lists no capture of the insulins page."],
    ["Scotland", "GGC predecessor formulary", "https://ggcmedicines.org.uk/formulary/endocrine-system-6/drugs-used-in-diabetes/",
     "archived copy read", "Live URL returns 404 after the move to WoS; read the Wayback capture of 10/12/2025."],
    ["Scotland", "Forth Valley predecessor formulary", "https://pharmacies.nhsforthvalley.com/wp-content/uploads/sites/6/2019/03/BNF6-Endocrine.pdf",
     "archived copy read", "Live PDF (created 30/07/2026) now holds only retained non-WoS sections; read the Wayback capture of 02/04/2023 (\"Last amended December 22\"). Later pre-WoS versions not captured."],
]
with open("access_log.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["nation", "item", "url", "outcome", "detail"])
    w.writerows(national)
print(len(rows), "rows;", len(national), "log entries")
