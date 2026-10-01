"""Write eu_withdrawals.csv from the source records read on 1 October 2026.

Each row was transcribed by hand from a capture in captures/. The reason_quoted field holds the
source's own wording, copied from the capture; where a source gives no reason, the field says so
in square brackets. Rows are kept here rather than typed into the CSV so that quoting and
punctuation (curly apostrophes, semicolons, pipes) survive intact.

Run: python3 build_eu_withdrawals.py
"""
import csv
from pathlib import Path

READ_ON = "2026-10-01"
NONE = "[no reason given in source]"

EMA = "https://www.ema.europa.eu"
ROWS = [
    # ---------------- EU / EEA-wide ----------------
    ("EU/EEA", "Fiasp", "all presentations (marketing authorisation)",
     "No withdrawal of marketing authorisation; EMA page shows status Authorised; 13 presentations authorised incl. FlexTouch (001-006), vial (007-009), Penfill (010-011), PumpCart 1.6 ml (012-013)",
     "2026-10-01 (status at reading); presentations list last updated 2020-06-15", NONE,
     f"{EMA}/en/medicines/human/EPAR/fiasp ; {EMA}/en/documents/all-authorised-presentations/fiasp-epar-all-authorised-presentations_en.pdf"),
    ("EU/EEA", "Lyumjev", "all presentations (marketing authorisation)",
     "No withdrawal of marketing authorisation; status Authorised; 15 presentations remain (vials, cartridges, KwikPen 100 and 200); Tempo Pen (016-017) absent after deletion",
     "2026-10-01 (status at reading); presentations list last updated 2026-07-13", NONE,
     f"{EMA}/en/medicines/human/EPAR/lyumjev ; {EMA}/en/documents/all-authorised-presentations/lyumjev-epar-all-authorised-presentations_en.pdf"),
    ("EU/EEA", "Lyumjev", "Tempo Pen 100 U/ml (EU/1/20/1422/016, 017)",
     "Presentation deleted from the marketing authorisation (variation C.7.a, type IB, worksharing with Humalog and Abasaglar Tempo Pen); completed",
     "2026-07-09", NONE,
     f"{EMA}/en/documents/procedural-steps-after/lyumjev-epar-procedural-steps-taken-scientific-information-after-authorisation_en.pdf"),
    ("EU/EEA", "Humalog", "Tempo Pen 100 U/ml (EU/1/96/007/046, 047)",
     "Presentation deleted from the marketing authorisation in the same worksharing variation as Lyumjev Tempo Pen; completed",
     "2026-07-09", NONE,
     f"{EMA}/en/documents/procedural-steps-after/humalog-epar-procedural-steps-taken-scientific-information-after-authorisation_en.pdf"),
    ("EU/EEA", "Liprolog; Humalog; NovoRapid; Apidra; Insulin aspart Sanofi; Insulin lispro Sanofi; Kirsty",
     "all presentations (marketing authorisation)",
     "No withdrawal of marketing authorisation; each EMA page shows status Authorised. No EMA page exists under the names Admelog or Trurapi (EU names are Insulin lispro Sanofi and Insulin aspart Sanofi)",
     "2026-10-01 (status at reading)", NONE,
     f"{EMA}/en/medicines/human/EPAR/liprolog ; {EMA}/en/medicines/human/EPAR/humalog ; {EMA}/en/medicines/human/EPAR/novorapid ; {EMA}/en/medicines/human/EPAR/apidra ; {EMA}/en/medicines/human/EPAR/insulin-aspart-sanofi ; {EMA}/en/medicines/human/EPAR/insulin-lispro-sanofi ; {EMA}/en/medicines/human/EPAR/kirsty"),
    ("EU/EEA", "Fiasp", "PumpCart 100 U/ml, 1.6 ml cartridge",
     "MAH informed EMA of planned discontinuation by end 2026 (with Levemir, NovoMix 50, Mixtard 50 and older human-insulin presentations); proposal stage",
     "2024-11-20", NONE + " (slide lists products only)",
     f"{EMA}/en/documents/presentation/presentation-feedback-spoc-working-party-activities-glp-1-receptor-agonists-insulin-products-shortage-management-k-kruttwig_en.pdf"),
    ("EU/EEA (Belgium, Denmark, Finland, France, Germany, Ireland, Luxembourg, Netherlands, Norway, Spain, Sweden named as affected)",
     "Fiasp", "PumpCart 100 U/ml, 1.6 ml cartridge",
     "Intermittent shortage (start 2025-05-08) plus announced permanent discontinuation in all EU/EEA countries where marketed, by end 2026 at latest",
     "2025-05-12 (first published); last updated 2025-12-18",
     "Shortage: \"The current manufacturing capacity for Fiasp PumpCart cannot meet demand.\" | Discontinuation: \"the company marketing Fiasp will discontinue Fiasp PumpCart for commercial reasons by the end of 2026 at the latest in all EU/EEA countries where the product is currently marketed.\"",
     f"{EMA}/en/medicines/human/shortages/fiasp-pumpcart-insulin-aspart"),
    ("EU/EEA", "Fiasp", "PumpCart 100 U/ml, 1.6 ml cartridge",
     "Medicine shortage communication (EU template) announcing shortage and cessation of marketing",
     "2025-05-12",
     "\"In addition, due to commercial reasons, marketing of Fiasp PumpCart will cease by the end of 2026 at the latest in all EU/EEA countries where the product is currently marketed.\"",
     f"{EMA}/en/documents/other/medicine-shortage-communication-msc-fiasp-pumpcart-novorapid-pumpcart_en.pdf"),
    ("EU/EEA", "Fiasp", "PumpCart only (other Fiasp presentations not listed)",
     "Listed in EMA notice of Novo Nordisk insulin discontinuations in all Member States where marketed, before end 2026; NovoRapid and Fiasp FlexTouch are not listed",
     "2025-10-31 (first published); last updated 2026-05-27",
     "\"The company Novo Nordisk has decided to stop marketing some of its insulins for commercial reasons. This decision is not related to a quality defect or safety issue.\"",
     f"{EMA}/en/medicines/human/shortages/novonordisk-insulin-human-insulin-various-short-rapid-intermediate-mixed-long-acting-forms"),
    ("EU/EEA (country-specific)", "Lyumjev; Humalog; Liprolog (also Humulin, Humalog Mix, Abasaglar)",
     "Lyumjev 100 U/ml cartridge, vial, KwikPen, Junior KwikPen; Lyumjev 200 U/ml KwikPen; Humalog and Liprolog cartridge, vial, KwikPen, Junior KwikPen (which apply varies by country; template allows 'none' remaining)",
     "Announced national discontinuations in selected EU/EEA countries, all before Q2 2027 (EMA lists under shortages)",
     "2026-03-23 (first published)",
     "\"The company Eli Lilly has decided to stop marketing some of its insulin medicines for commercial reasons. This decision is not related to a quality defect or safety issue.\"",
     f"{EMA}/en/medicines/human/shortages/eli-lilly-insulin-various-forms"),
    ("EU/EEA (country-specific)", "Lyumjev; Humalog; Liprolog", "as row above",
     "Medicine shortage communication template (agreed by SPOC WP 2026-03-09, MSSG 2026-03-16) for national discontinuation letters",
     "2026-03-16",
     "\"After careful consideration and a thorough market assessment, Eli Lilly and Company (Lilly) [...] is notifying healthcare professionals about the discontinuation of the following presentations of its insulin formulations\" | \"The discontinuations are not a consequence of any safety, efficacy, or quality related issue.\"",
     f"{EMA}/en/documents/other/medicine-shortage-communication-msc-insulin-human-insulin-various-short-rapid-intermediate-mixed-long-acting-forms-2026_en.pdf"),
    ("EU/EEA (Austria, Belgium, Czechia, Denmark, Finland, France, Germany, Italy, Luxembourg, Netherlands, Norway, Portugal, Slovakia, Slovenia, Spain, Sweden)",
     "NovoRapid", "PumpCart 100 U/ml, 1.6 ml cartridge",
     "Shortage only (intermittent); presentation retained",
     "2025-05-08 (start); last updated 2025-12-18",
     "\"The current manufacturing capacity for NovoRapid PumpCart cannot meet demand.\"",
     f"{EMA}/en/medicines/human/shortages/novorapid-pumpcart-insulin-aspart"),

    # ---------------- Germany ----------------
    ("Germany", "Fiasp", "PumpCart",
     "Discontinuation announced for 2026 in Novo Nordisk letter on older insulins (Levemir, Actrapid, Actraphane, Protaphane)",
     "2024-09 (letter; BfArM file dated 2024-09-27)",
     "\"Die Angebotsanpassung ist Teil einer globalen Initiative von Novo Nordisk. Auch in anderen Ländern werden frühe Therapien auslaufen, um Verfügbarkeit und Einsatz moderner Therapien weltweit zu stärken.\" | \"2026 wird auch die Fiasp® PumpCart® auslaufen, während NovoRapid® PumpCart® im Bestand bleibt.\"",
     "https://www.bfarm.de/SharedDocs/Downloads/DE/Arzneimittel/Zulassung/amInformationen/Lieferengpaesse/info_insuline_20240927.pdf?__blob=publicationFile"),
    ("Germany", "Fiasp", "PumpCart",
     "Medical society press release (DGE, Prof. Helmut Schatz) on the announced discontinuation; describes the presentation as little used",
     "2025-03-10",
     "\"Fiasp®PumpCart® (Insulin aspart), welches sehr wenig eingesetzt wurde, wird allerdings ab 2027 auch nicht mehr erhältlich sein.\" [statement by the DGE author, citing Novo Nordisk 'DiabeTICKER'; the manufacturer's own wording was not found]",
     "https://blog.endokrinologie.net/aeltere-insulinpraeparate-novo-nordisk-nicht-mehr-verfuegbar-5765/"),
    ("Germany", "Fiasp", "PumpCart",
     "Shortage plus discontinuation brought forward: available in 2025 only in continuously decreasing quantities; vial, Penfill and FlexTouch retained",
     "2025-05 (letter); AMK 26/25 published 2025-06-23",
     "\"Die Produktionskapazität kann die derzeitige Nachfrage nach Fiasp® PumpCart® und NovoRapid® PumpCart® nicht decken.\" | \"In allen EU/EWR-Ländern war bereits geplant, Fiasp® PumpCart® bis Ende 2026 einzustellen. Um eine stabile Versorgung mit NovoRapid® PumpCart® sicherzustellen, wird die Belieferung in Deutschland auf NovoRapid® PumpCart® konzentriert.\"",
     "https://www.diabetikerbund-bayern.de/fileadmin/content/_Media/Info-Brief_NovoNordisk_zu_Fiasp_und_NovoRapid.pdf ; https://www.abda.de/fuer-apotheker/arzneimittelkommission/amk-nachrichten/detail/26-25-information-der-hersteller-informationsschreiben-zu-fiaspr-pumpcartr-und-novorapidr-pumpcartr-insulin-aspart-moegliche-engpaesse-und-vorgezogene-geplante-vertriebseinstellung-von-fiaspr-pumpcartr/"),
    ("Germany", "Fiasp", "PumpCart",
     "Discontinuation confirmed: restricted availability until end 2025; FlexTouch, Penfill and vial listed as remaining available",
     "2025-10 (letter); BfArM published 2025-11-03",
     "\"Der Vertrieb dieser Insuline wird in allen EU-/EWR-Ländern eingestellt.\" | \"Die Einstellung ist nicht auf sicherheits- oder qualitätsbezogene Probleme zurückzuführen.\"",
     "https://www.bfarm.de/SharedDocs/Downloads/DE/Arzneimittel/Zulassung/amInformationen/Lieferengpaesse/msc_insuline.pdf?__blob=publicationFile"),
    ("Germany", "Lyumjev", "KwikPen and cartridges, 5-pack size only (10-packs and Junior KwikPen retained)",
     "Pack size withdrawn; marketing ended by end 2025, remaining stock sold in Q1 2026; completed",
     "2025-12-31 (end of marketing); letter 2026-04-16",
     "\"Die Markteinstellungen erfolgen nicht aufgrund von Sicherheits-, Wirksamkeits- oder Qualitätsbedenken.\" " + NONE.replace("]", " beyond this]"),
     "https://www.bfarm.de/SharedDocs/Downloads/DE/Arzneimittel/Zulassung/amInformationen/Lieferengpaesse/info_insuline_lily.pdf?__blob=publicationFile"),
    ("Germany", "Humalog", "KwikPen and cartridges, 5-pack size only (Junior KwikPen retained)",
     "Pack size withdrawn; completed end 2025", "2025-12-31; letter 2026-04-16",
     "\"Die Markteinstellungen erfolgen nicht aufgrund von Sicherheits-, Wirksamkeits- oder Qualitätsbedenken.\"",
     "https://www.bfarm.de/SharedDocs/Downloads/DE/Arzneimittel/Zulassung/amInformationen/Lieferengpaesse/info_insuline_lily.pdf?__blob=publicationFile"),
    ("Germany", "Liprolog", "all (Liprolog, Liprolog 200, Mix25, Mix50)",
     "Whole brand withdrawn; completed end 2025 (Humalog named as identical alternative)", "2025-12-31; letter 2026-04-16",
     "\"Die Markteinstellungen erfolgen nicht aufgrund von Sicherheits-, Wirksamkeits- oder Qualitätsbedenken.\"",
     "https://www.bfarm.de/SharedDocs/Downloads/DE/Arzneimittel/Zulassung/amInformationen/Lieferengpaesse/info_insuline_lily.pdf?__blob=publicationFile"),

    # ---------------- France ----------------
    ("France", "Lyumjev", "100 U/ml cartridge (CIP 34009 3020396 5)",
     "Marketing cessation announced for 2026-04-30 (orders met until stock exhausted, end June 2026 at latest); Junior KwikPen 100, KwikPen 200 and vial named as remaining",
     "2025-06-27 (letter); effective 2026-04-30",
     "\"Dans le cadre de cet engagement envers les patients et afin de maintenir un approvisionnement continu et fiable des insulines les plus couramment utilisées par nos patients, nous avons pris la décision de rationaliser notre portefeuille d’insulines au niveau mondial.\" | \"Cette décision ne fait pas suite à des problèmes de sécurité ou d’efficacité de ces médicaments.\"",
     "https://medical.lilly.com/fr/products/answers/lettre-d-information-l-attention-des-m-decins-relatif-l-arr-t-de-commercialisation-de-certaines-pr-sentations-d-abasaglar-humalog-lyumjev-et-umuline-284223"),
    ("France", "Lyumjev", "100 U/ml cartridge",
     "Completed: VIDAL monograph marked 'Arrêt de commercialisation (30/04/2026)' and 'supprimé'", "2026-04-30", NONE,
     "https://www.vidal.fr/medicaments/lyumjev-100-u-ml-sol-inj-cart-212141.html"),
    ("France", "Fiasp", "PumpCart 100 U/ml",
     "Marketing cessation announced for 2026-12-31 (Novo Nordisk letter 2026-08-24); FIASP vial, FLEXTOUCH and PENFILL stated as not affected",
     "2026-09-08 (VIDAL); letter 2026-08-24",
     NONE + " (VIDAL cites EMA 'commercial reasons' only for Victoza)",
     "https://www.vidal.fr/actualites/38267-traitement-du-diabete-une-serie-d-arrets-de-commercialisation-chez-novo-nordisk.html"),
    ("France", "Fiasp", "PumpCart 100 U/ml",
     "Professional society notice of marketing cessation on 2026-12-31", "2026-04-13", NONE,
     "https://www.sfdiabete.org/actualites/medical-paramedical/rappel-arret-de-commercialisation-au-31-decembre-2026"),
    ("France", "Fiasp; NovoRapid", "PumpCart 100 U/ml",
     "Shortage only (supply tension); new initiations suspended to end 2025", "2025-08-12 (updated 2025-09-29)",
     "\"Les tensions sont liées à une augmentation des ventes de cartouches d’insuline, conjuguée à une capacité limitée de production du laboratoire, qui ne permet pas temporairement de répondre à la demande.\"",
     "https://ansm.sante.fr/actualites/tensions-dapprovisionnement-sur-les-cartouches-dinsuline-novo-nordisk-utilisees-avec-les-pompes-ypsopump-conduites-a-tenir"),
    ("France", "Fiasp", "PumpCart 100 U/ml",
     "Shortage entry closed: 'Remise à disposition normale depuis le 15/05/2026'", "2025-07-07 (published); 2026-05-15 (resolved)", NONE,
     "https://ansm.sante.fr/disponibilites-des-produits-de-sante/medicaments/fiasp-pumpcart-100-unites-ml-solution-injectable-en-cartouche-insuline-asparte-levure-saccharomyces-cerevisiae"),
    ("France", "Fiasp", "FlexTouch 100 U/ml pre-filled pen",
     "Shortage only; entry closed 'Remise à disposition normale depuis le 15/05/2026'", "2025-07-17 (published); 2026-05-15 (resolved)", NONE,
     "https://ansm.sante.fr/disponibilites-des-produits-de-sante/medicaments/fiasp-flextouch-100-unites-ml-solution-injectable-en-stylo-prerempli-insuline-asparte-levure-saccharomyces-cerevisiae"),

    # ---------------- Spain ----------------
    ("Spain", "Fiasp", "FlexTouch 100 U/ml, 5 pens",
     "Shortage only (supply problems since 2023, controlled distribution)", "2024-10-11",
     "\"Novo Nordisk también ha comunicado a la Agencia diferentes problemas de suministro desde 2023 de otras insulinas rápidas de su cartera de productos que, previsiblemente, se resolverán a comienzos de 2025\" " + NONE.replace("]", " for the shortage itself]"),
     "https://www.aemps.gob.es/informa/la-aemps-informa-del-cese-de-comercializacion-de-varias-insulinas/"),
    ("Spain", "Apidra", "100 U/ml vial, 10 ml",
     "Marketing cessation announced by Sanofi; other formats retained", "2024-10-11", NONE,
     "https://www.aemps.gob.es/informa/la-aemps-informa-del-cese-de-comercializacion-de-varias-insulinas/"),
    ("Spain", "Fiasp", "PumpCart 100 U/ml, 5 x 1.6 ml",
     "Marketing cessation in 2026 announced (with FlexTouch still in shortage); AEMPS also proposed prioritising fast aspart for type 1 diabetes", "2025-01-17",
     "\"Esta decisión, según informa el laboratorio, viene motivada por una reorganización de su cartera de productos y de sus capacidades de fabricación hacia productos más eficientes.\"",
     "https://www.aemps.gob.es/informa/la-aemps-en-colaboracion-con-las-sociedades-medicas-implicadas-en-el-tratamiento-de-la-diabetes-emite-recomendaciones-de-uso-de-las-insulinas-de-accion-rapida/"),
    ("Spain", "Fiasp; NovoRapid", "PumpCart 100 U/ml, 5 x 1.6 ml",
     "Active supply-problem entries in CIMA: Fiasp PumpCart from 2025-04-09, NovoRapid PumpCart (controlled distribution) from 2025-05-25, both with expected end 2026-12-30",
     "2025-04-09 / 2025-05-25", NONE,
     "https://cima.aemps.es/cima/rest/psuministro"),
    ("Spain", "Lyumjev", "Junior KwikPen 100, vial 100, Tempo Pen 100, KwikPen 200 (nationally listed)",
     "Authorised but flagged not marketed (comerc=false) for every listed presentation at reading; no cessation notice found, so whether it was ever marketed is not shown",
     "2026-10-01 (status at reading)", NONE,
     "https://cima.aemps.es/cima/rest/medicamentos?nombre=lyumjev"),

    # ---------------- Netherlands ----------------
    ("Netherlands", "Fiasp", "PumpCart 100 E/ml, 1.6 ml, 5 cartridges",
     "Listed as 'uit de handel' (withdrawn from the market)", "2026-10-01 (page last updated)",
     "Reden van tekort: \"Uit het assortiment genomen.\"",
     "https://farmanco.knmp.nl/geneesmiddel/4664.html"),
    ("Netherlands", "Fiasp", "FlexTouch",
     "Shortage only (temporary, expected back early September 2025)", "2025-08-05",
     "\"Op dit moment is er een tijdelijk tekort aan NovoRapid FlexPennen en Fiasp FlexTouch insulinepennen.\" " + NONE,
     "https://www.dvn.nl/nieuws/tijdelijk-tekort-novorapid-flexpennen-en-fiasp-flextouch"),

    # ---------------- Belgium ----------------
    ("Belgium", "Fiasp", "PumpCart 100 U/ml",
     "Shortage plus announced cessation of marketing by end 2026 in all European countries where marketed (national MSC)", "2025-05-09",
     "\"De plus, à des fins d'optimisation de la production, la commercialisation de Fiasp® PumpCart® s’arrêtera au plus tard fin 2026 dans tous les pays européens où le produit est actuellement commercialisé.\"",
     "https://app.fagg-afmps.be/pharma-status/api/files/6842d635cfba3d0f2ab38454"),
    ("Belgium", "Fiasp", "PumpCart 100 U/ml, 5 x 1.6 ml",
     "PharmaStatus: 'Stop of commercialisation' from 2026-12-31 (FlexTouch 10 x 3 ml, Penfill and vial listed Available)", "2026-01-21 (notification published)",
     "Reason field: \"Other reason\"",
     "https://pharmastatus.be/api/notifications/export/public?language=en"),
    ("Belgium", "Lyumjev", "100 U/ml cartridge, 5 x 3 ml",
     "PharmaStatus: 'Stop of commercialisation' from 2026-03-31 (vial, KwikPen 100, Junior KwikPen and KwikPen 200 listed Available)", "2025-05-30 (notification published)",
     "Reason field: \"Other reason\"",
     "https://pharmastatus.be/api/notifications/export/public?language=en"),

    # ---------------- Denmark ----------------
    ("Denmark", "Fiasp", "PumpCart 100 enheder/ml",
     "Permanent cessation of marketing ('Permanent markedsophør') from mid-October 2026", "2026-07-21",
     "Årsag: \"Kommercielle årsager\"",
     "https://laegemiddelstyrelsen.dk/da/godkendelse/kontrol-og-inspektion/mangel-paa-medicin/meddelelser-om-forsyning-af-medicin/human-2026/fiasp-pumpcart-100-enhederml-forsyningsvanskelighed"),
    ("Denmark", "Fiasp", "PumpCart 100 enheder/ml",
     "Shortage only (early June to early July 2026); resolved", "2026-06-08 (updated 2026-07-08)",
     "Årsag: \"Øget salg/efterspørgsel\"",
     "https://laegemiddelstyrelsen.dk/da/godkendelse/kontrol-og-inspektion/mangel-paa-medicin/meddelelser-om-forsyning-af-medicin/human-2026/fiasp-pumpcart-forsyningsvanskelighed"),
    ("Denmark", "NovoRapid", "FlexTouch 100 E/ml",
     "Permanent cessation of marketing from end July 2025", "2025-06-16",
     "Årsag: \"Kommercielle årsager\"",
     "https://laegemiddelstyrelsen.dk/da/godkendelse/kontrol-og-inspektion/mangel-paa-medicin/meddelelser-om-forsyning-af-medicin/human-2025/novorapid-flex-touch-forsyningsvanskelighed/"),

    # ---------------- Norway ----------------
    ("Norway", "Fiasp", "PumpCart (vial, FlexTouch and Penfill not affected)",
     "Deregistration ('avregistrering') during 2026 as part of Novo Nordisk discontinuations", "2025-03-27 (published); updated 2026-09-16",
     "\"Firmaet oppgir kommersielle årsaker til at produksjon og salg avsluttes. De fleste produktene har lavt salg og er lite lønnsomme. Avregistreringene gjelder i hele Europa, ikke bare i Norge.\" [second sentence is the agency's statement about the set of products, not specific to Fiasp PumpCart]",
     "https://www.dmp.no/forsyningssikkerhet/legemiddelmangel/nyheter/Diabeteslegemidler-avregistreres"),
    ("Norway", "Lyumjev", "KwikPen 200 E/ml; Junior KwikPen 100 E/ml",
     "Withdrawn 2025-10-01 (Lyumjev KwikPen 100 E/ml named as alternative); completed", "2025-10-01; letter 2026-04-14", NONE,
     "https://www.legeforeningen.no/contentassets/007bc46ac76641fd8a8cdca2753f298b/brev-til-fastleger-om-utfasing-av-insulin-april-2026_endelig.pdf"),
    ("Norway", "Lyumjev", "KwikPen / Junior KwikPen (vial, cartridge and prefilled pen stated as not affected)",
     "Listed among insulins deregistered in 2025 or early 2026", "2026-06-30 (updated 2026-07-03)",
     "\"Dette skyldes i hovedsak kommersielle forhold, og gjelder i hele Europa.\" [general statement covering all listed insulins]",
     "https://www.legemidlertilbarn.no/nyheter/insuliner-som-utgar-i-2026"),
    ("Norway", "Lyumjev", "200 E/ml",
     "Listed in Felleskatalogen discontinued products 2026; 100 E/ml still described", "2026", NONE,
     "https://www.felleskatalogen.no/medisin/utgatte-preparater"),
    ("Norway", "Apidra", "SoloStar pre-filled pen (whole remaining product)",
     "Deregistered spring 2026; Felleskatalogen 2026 lists Apidra injection as discontinued", "2026 (spring)",
     "NEF/NFA comment: \"Lite brukt generelt\" [clinical associations' description, not a manufacturer reason]",
     "https://www.legeforeningen.no/contentassets/007bc46ac76641fd8a8cdca2753f298b/brev-til-fastleger-om-utfasing-av-insulin-april-2026_endelig.pdf ; https://www.felleskatalogen.no/medisin/utgatte-preparater"),
    ("Norway", "Apidra", "cartridge and vial",
     "Listed in Felleskatalogen discontinued products 2023 (pre-filled pen still described)", "2023", NONE,
     "https://www.felleskatalogen.no/medisin/utgatte-preparater/2023"),

    # ---------------- Finland ----------------
    ("Finland", "Fiasp", "PumpCart 100 U/ml, 5 x 1.6 ml (other Fiasp 100 U/ml products not affected)",
     "Manufacture and sale to end by 2026-12-31; national MSC on shortage and withdrawal sent 2025-05-06", "2026-04-29 (Fimea notice)",
     "\"Päätös perustuu yhtiön liiketoiminnallisiin syihin, eikä liity valmisteiden laatuun tai turvallisuuteen.\"",
     "https://fimea.fi/-/levemir-ja-fiasp-pumpcart-insuliinivalmisteet-poistuvat-markkinoilta-vuoden-2026-lopussa"),

    # ---------------- Sweden ----------------
    ("Sweden", "Fiasp", "PumpCart and FlexTouch",
     "Reported by patient organisation magazine as among insulins Novo Nordisk would stop selling, planned completion Q3 2025 (proposal at time of report)", "2024-12-27",
     "\"Företaget anger som skäl att de vill ”optimera” produktionen och ”bättre möta patientefterfrågan”.\" [Dagens Diabetes quoting Allt om diabetes, Svenska Diabetesförbundet, nr 1 2025]",
     "https://dagensdiabetes.se/insulinforetag-slutar-att-producera-flera-insulin-2025/"),
    ("Sweden", "Fiasp", "FlexTouch 100 enheter/ml pre-filled pen (vial and Penfill remain)",
     "Withdrawn from the market ('har utgått från marknaden'); completed", "2025-10-13", NONE + " (regional prescribing-support page, not the national agency)",
     "https://samverkan.regionsormland.se/for-vardgivare/lakemedel/lakemedelsrester/avregistrerade-lakemedel/"),

    # ---------------- Italy ----------------
    ("Italy", "Insulin lispro Sanofi", "100 U/ml cartridge 3 ml, 5 cartridges",
     "AIFA shortage list: temporary cessation of marketing ('Cessata commercializzazione temporanea') from 2026-09-30", "2026-09-30",
     "Motivazioni: \"Cessata commercializzazione temporanea\"",
     "https://www.aifa.gov.it/documents/20142/847339/elenco_medicinali_carenti.csv"),

    # ---------------- Switzerland ----------------
    ("Switzerland", "Lyumjev", "100 IE/ml vial 10 ml; cartridges 5 x 3 ml; KwikPen 100 5 x 3 ml",
     "Distribution cessation reported (mutation 2026-01-26); out of trade ('Ausser Handel') from 2026-03-01; no Lyumjev presentation found in the active out-of-trade list beyond these three", "2026-03-01",
     NONE, "https://www.drugshortage.ch/index.php/ausser-handel-2/ ; https://www.drugshortage.ch/index.php/registriert-nicht-mehr-im-verkauf-2/"),
    ("Switzerland", "NovoRapid", "FlexTouch 5 x 3 ml",
     "Out of trade ('Ausser Handel') from 2026-03-31", "2026-03-31", NONE,
     "https://www.drugshortage.ch/index.php/ausser-handel-2/"),
]

COLS = ["jurisdiction", "product", "presentation", "event", "date", "reason_quoted", "source_url", "read_on"]


def main():
    out = Path(__file__).with_name("eu_withdrawals.csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for r in ROWS:
            assert len(r) == 7, r
            w.writerow(list(r) + [READ_ON])
    print(f"wrote {len(ROWS)} rows to {out}")


if __name__ == "__main__":
    main()
