"""Write route.csv: the regulatory and market route of long-acting and ultra-rapid insulin analogues
in Germany, one row per decision or notice, each with a verbatim quote and the capture it came from.

The rows were assembled by hand from the documents in captures/. This script checks that every quote
occurs in the text version of its capture (after collapsing whitespace and removing soft hyphenation
at line ends), so a quote cannot drift from its source unnoticed. A row whose quote is not found
stops the build.
"""
import csv, re
from pathlib import Path

HERE = Path(__file__).parent
CAP = HERE / "captures"
G = "https://www.g-ba.de"
R = [
 # product, body, decision, date, quote, url, capture (stem; .txt is checked)
 ("Tresiba (insulin degludec)", "IQWiG", "Dossier assessment A14-13: added benefit not proven, type 1 and type 2", "2014-07-30",
  "Zusatznutzen nicht belegt", G + "/downloads/92-975-505/2014-07-30_A14-13_Insulin-degludec_Nutzenbewertung-35a-SGB-V.pdf", "degludec_iqwig_A14-13_2014-07-30"),
 ("Tresiba (insulin degludec)", "G-BA", "AMNOG Beschluss D-109 (adults, type 2 subgroups and type 1): no added benefit", "2014-10-16",
  "Ein Zusatznutzen ist nicht belegt.", G + "/bewertungsverfahren/nutzenbewertung/109/", "degludec_gba_2014-10-16_beschluss_D109"),
 ("Tresiba (insulin degludec)", "G-BA", "AMNOG Beschluss D-118 (combination with GLP-1 RA, no dossier): no added benefit", "2014-12-04",
  "Der Zusatznutzen gilt als nicht belegt.", G + "/bewertungsverfahren/nutzenbewertung/121/", "degludec_gba_2014-12-04_beschluss_D118"),
 ("Tresiba (insulin degludec)", "Pharmazeutische Zeitung", "Withdrawal announced after arbitration board set price at human insulin level", "2015-07-08",
  "Kürzlich habe nun eine Schiedsstelle festgelegt, Tresiba dürfe nicht mehr kosten als eine herkömmliche Therapie mit Humaninsulin.",
  "https://www.pharmazeutische-zeitung.de/ausgabe-282015/ab-oktober-nur-noch-als-import/", "degludec_pz_2015-28_nur-noch-import"),
 ("Tresiba (insulin degludec)", "G-BA", "AMNOG Beschluss D-158 (children from 1 year): no added benefit", "2015-08-20",
  "Ein Zusatznutzen ist nicht belegt.", G + "/bewertungsverfahren/nutzenbewertung/162/", "degludec_gba_2015-08-20_beschluss_D158"),
 ("Tresiba (insulin degludec)", "Deutsche Apotheker Zeitung", "Withdrawal postponed", "2015-09-29",
  "doch nicht wie angekündigt Anfang Oktober außer Vertrieb nehmen",
  "https://www.deutsche-apotheker-zeitung.de/news/artikel/2015/09/29/hersteller-verlangert-ubergangsfrist-fur-tresiba", "degludec_daz_2015-09-29_uebergangsfrist"),
 ("Tresiba (insulin degludec)", "Deutsche Apotheker Zeitung", "Distribution in Germany ends 15 January 2016", "2015-12-16",
  "den Vertrieb in Deutschland zum 15. Januar einzustellen",
  "https://www.deutsche-apotheker-zeitung.de/news/artikel/2015/12/16/endgultiges-aus-fur-tresiba", "degludec_daz_2015-12-16_endgueltiges-aus"),
 ("Xultophy (degludec/liraglutide)", "G-BA", "AMNOG Beschluss D-165: no added benefit", "2015-10-15",
  "Ein Zusatznutzen ist nicht belegt.", G + "/bewertungsverfahren/nutzenbewertung/168/", "degludec_xultophy_gba_2015-10-15_beschluss_D165"),
 ("Xultophy (degludec/liraglutide)", "Deutsche Apotheker Zeitung", "Distribution in Germany ends 1 August 2016", "2016-06-16",
  "den Vertrieb des Antidiabetikums zum 1. August 2016 einstellen",
  "https://www.deutsche-apotheker-zeitung.de/news/artikel/2016/06/16/xultophy-vetrieb-wird-eingestellt", "degludec_xultophy_daz_2016-06-16_vertrieb-eingestellt"),
 ("Tresiba (insulin degludec)", "G-BA", "Re-assessment ordered on DEVOTE cardiovascular outcome data", "2018-02-15",
  "Falls Tresiba® zu diesem Zeitpunkt nicht auf dem deutschen Markt verfügbar sein sollte",
  G + "/downloads/40-268-4807/", "degludec_gba_2018-02-15_veranlassung_TrG"),
 ("Tresiba (insulin degludec)", "arznei-telegramm", "Back on the market from December 2018", "2019-02-15",
  "wieder im Handel", "https://www.arznei-telegramm.de/html/2019_02/1902017_02.html", "degludec_arznei-telegramm_2019-02"),
 ("Tresiba (insulin degludec)", "G-BA", "Re-assessment D-405 (adults, type 2, with DEVOTE): no added benefit", "2019-05-16",
  "Ein Zusatznutzen ist nicht belegt.", G + "/bewertungsverfahren/nutzenbewertung/415/", "degludec_gba_2019-05-16_beschluss_D405"),
 ("Tresiba (insulin degludec)", "G-BA", "Tragende Gründe D-405 record the relaunch date", "2019-05-16",
  "wurde zum 1. Dezember 2018 erneut in Verkehr gebracht", G + "/downloads/40-268-5746/", "degludec_gba_2019-05-16_TrG_D405"),
 ("Tresiba (insulin degludec)", "APOTHEKE ADHOC", "Erstattungsbetrag agreed; listed price unchanged", "2019-08-22",
  "Der gelistete Abgabepreis des Basalinsulins liegt nun unverändert bei 73,20 Euro.",
  "https://www.apotheke-adhoc.de/nachrichten/detail/pharmazie/erstattungsbetrag-fuer-tresiba-diabetes/", "degludec_adhoc_erstattungsbetrag"),
 ("Tresiba (insulin degludec)", "GKV-Spitzenverband", "Erstattungsbetrag listed as agreed (page updated 2019-09-13)", "2019-09-13",
  "Erstattungsbetrag vereinbart", "https://www.gkv-spitzenverband.de/ (Erstattungsbetrag database, Wirkstoff 298176; full path not recorded in capture)", "degludec_gkvsv_ebv_wirkstoff_298176"),
 ("Tresiba (insulin degludec)", "Shop Apotheke (online pharmacy listing)", "Marketed now: PZN 14362600 FlexTouch 200 5x3 ml listed as prescription-only and available (read 2026-10-02)", "2026-10-02",
  "verschreibungspflichtiges Arzneimittel", "https://www.shop-apotheke.com/arzneimittel/14362600/tresiba-flextouch-200-i-e-ml.htm", "degludec_shop-apotheke_tresiba_14362600"),
 ("Toujeo (glargine 300)", "G-BA", "No §35a procedure: not a new active substance; none of 1,387 listed procedures concerns Toujeo, Fiasp or Lyumjev (list read 2026-10-02)", "2026-10-02",
  "Der Gemeinsame Bundesausschuss bewertet den Nutzen aller erstattungsfähigen Arzneimittel mit neuen Wirkstoffen.",
  "https://www.gesetze-im-internet.de/sgb_5/__35a.html", "toujeo_sgb5_35a"),
 ("Toujeo (glargine 300)", "Deutsches Ärzteblatt", "On the German market by December 2015 (exact launch date not confirmed)", "2015-12-11",
  "das neue Mittel Toujeo, das in Deutschland und den USA hervorragend gestartet sei",
  "https://www.aerzteblatt.de/news/sanofi-investiert-weiter-in-frankfurt-hoechst-bf3cee35-6eca-4dc2-9f98-4206d5499c55", "toujeo_aerzteblatt_sanofi-hoechst"),
 ("Toujeo (glargine 300)", "G-BA", "AM-RL Anlage III: long-acting analogues in type 2 not prescribable while dearer than NPH human insulin", "2010-03-18",
  "mit Mehrkosten im Vergleich zu intermediär wirkendem Humaninsulin verbunden sind",
  G + "/downloads/39-261-1109/2010-03-18-AMR3_Insulinanaloga_Typ2_BAnz.pdf", "toujeo_gba_2010-03-18_AMR3_Insulinanaloga_Typ2_BAnz"),
 ("Fiasp (faster aspart)", "Deutsches Ärzteblatt (supplement)", "Launch in Germany", "2017-04-01",
  "Mit Fiasp steht seit dem 1. April 2017 ein neues Mahlzeiteninsulin in Deutschland zur Verfügung.",
  "https://www.aerzteblatt.de/archiv/neues-mahlzeiteninsulin-fiasp-bei-diabetes-mellitus-52c37a2b-6a57-4ba6-860d-c72c44c66c91", "fiasp_aerzteblatt_neues-mahlzeiteninsulin"),
 ("Fiasp (faster aspart)", "G-BA", "AMR Anlage 10: short-acting analogues in type 2 not prescribable while dearer than human insulin", "2006-07-18",
  "nicht verordnungsfähig, solange sie mit Mehrkosten im Vergleich zu kurzwirksamem Humaninsulin verbunden sind",
  G + "/downloads/39-261-313/2006-07-18-AMR-Insulinanaloga_BAnz.pdf", "fiasp_gba_2006-07-18_AMR_Insulinanaloga_BAnz"),
 ("Fiasp (faster aspart)", "APOTHEKE ADHOC", "Fiasp PumpCart discontinued; pens, cartridges and vials continue", "2025-11-11",
  "Das Fertigarzneimittel Fiasp Pumpcart wird eingestellt", "https://www.apotheke-adhoc.de/nachrichten/detail/pharmazie/insulin-aus-fuer-drei-sorten/", "fiasp_aa_insulin-aus-drei-sorten"),
 ("Lyumjev (lispro, treprostinil/citrate)", "Deutsches Ärzteblatt (supplement)", "Planned launch September 2020 (exact day not confirmed)", "2020-09",
  "ab September 2020", "https://www.aerzteblatt.de/archiv/lyumjev-r-in-der-eu-zugelassen-neu-und-schnell-28aa9bc0-4bc1-403a-8295-3bc1842d16be", "lyumjev_aerzteblatt_eu-zugelassen"),
 ("Lyumjev (lispro, treprostinil/citrate)", "Eli Lilly, in G-BA Zusammenfassende Dokumentation §40c", "Existing §130a(8) rebate contracts cover Humalog, Lyumjev and Abasaglar", "2025-12-04",
  "Auf Grundlage der bereits bestehenden Rabattverträge für unsere Produkte Humalog®, Lyumjev® und Abasaglar®",
  G + "/downloads/40-268-12140/2025-12-04_AM-RL_Paragraf-40-c_Austausch-Biologika-Apotheke_ZD.pdf", "lyumjev_gba_2025-12-04_AM-RL_40c_ZD"),
 ("Lyumjev (lispro, treprostinil/citrate)", "G-BA, Zusammenfassende Dokumentation §40c", "No biosimilar of Lyumjev authorised, so no pharmacy substitution", "2025-12-04",
  "zu den beiden (Referenz-)Arzneimitteln Lyumjev und Huminsulin bislang keine Biosimilars zugelassen sind",
  G + "/downloads/40-268-12140/2025-12-04_AM-RL_Paragraf-40-c_Austausch-Biologika-Apotheke_ZD.pdf", "lyumjev_gba_2025-12-04_AM-RL_40c_ZD"),
 ("Lyumjev (lispro, treprostinil/citrate)", "APOTHEKE ADHOC", "Still distributed (KwikPen in 10-packs only)", "2026-04-27",
  "werden aber weiterhin ausschließlich in 10er-Packungen vertrieben", "https://www.apotheke-adhoc.de/nachrichten/detail/pharmazie/insuline-restbestaende-abverkauft/", "lyumjev_aa_restbestaende"),
 ("All insulin analogues", "G-BA", "Anlage III type 2 restrictions still in force; cost judged on what the sickness fund actually pays", "2026-09-05",
  "Für die Bestimmung der Mehrkosten sind die der zuständigen Krankenkasse tatsächlich entstehenden Kosten maßgeblich.",
  G + "/downloads/83-691-1109/AM-RL-III-Verordnungeinschraenkungen_2026-09-05.pdf", "toujeo_gba_AM-RL-III_2026-09-05"),
 ("Human insulin and analogues (Festbetrag)", "G-BA", "Stufe 2 reference price group including analogues adopted", "2013-02-21",
  "Humaninsulin und Analoga, schnell wirkend", G + "/beschluesse/1661/", "festbetrag_gba_2013-02-21_AM-RL-IX-X_Humaninsulin-Analoga"),
 ("Human insulin and analogues (Festbetrag)", "BMG", "Ministry objects to the group (Beanstandung)", "2013-03-28",
  "beanstandet", G + "/beschluesse/1661/", "festbetrag_gba_2013-02-21_AM-RL-IX-X_Humaninsulin-Analoga_BMG"),
 ("Human insulin and analogues (Festbetrag)", "G-BA", "Group withdrawn", "2013-04-19",
  "zu Humaninsulin und Analoga zurück", G + "/beschluesse/1692/", "festbetrag_gba_2013-04-19_AM-RL_IX-X_Aufhebung_TrG"),
 ("Human insulin (Festbetrag)", "G-BA", "Stufe 1 groups Humaninsulin 1 to 3 formed; analogues not included", "2014-09-18",
  "Humaninsulin, Gruppe 3", G + "/beschluesse/2068/", "festbetrag_gba_2014-09-18_AM-RL-IX_Humaninsulin_G1-3S1_BAnz"),
 ("Insulin analogues (pharmacy substitution)", "G-BA", "§40c AM-RL: substitution of biologics in pharmacies, from 2026-04-01; Fiasp, Lyumjev, Toujeo listed as originals in Anlage VIIa", "2025-12-04",
  "ist eine Ersetzung nur möglich, wenn das in der Fachinformation angegebene Behältnis",
  G + "/beschluesse/7564/", "festbetrag_gba_2025-12-04_AM-RL_Paragraf-40-c_Austausch-Biologika-Apotheke_BAnz"),
]

norm = lambda s: re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", s)).replace("„", '"').replace("“", '"')
bad = 0
for row in R:
    txt = CAP / (row[6] + ".txt")
    if not txt.exists():
        print("MISSING capture", row[6]); bad += 1; continue
    if norm(row[4]) not in norm(txt.read_text(errors="replace")):
        print("QUOTE NOT FOUND", row[6], "|", row[4]); bad += 1
assert not bad, f"{bad} rows failed"
with open(HERE / "route.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["product", "body", "decision", "date", "quote", "url", "capture"])
    for r in R:
        w.writerow(list(r[:6]) + ["captures/" + r[6] + ".txt"])
print(len(R), "rows")
