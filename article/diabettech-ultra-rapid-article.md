# Losing Lyumjev: how the system let its patients down

*The usual preamble. This is analysis of published dispensing data, published trials and public
statements, not advice about which insulin anyone should use. The method, every number and the code
that produces them are in the [repository](https://github.com/tim2000s/rapid-insulin-prescribing),
and the sources are listed at the end.*

---

As MiniMed, Insulet, Tandem and CamDiab work to bring fully closed loop, a system that needs no meal
boluses at all, into wider use, the system that decides which insulins people are offered has
conspired to take away a key part of that equation: the fastest-absorbed subcutaneous mealtime insulin available. This
is a story of inertia, ineptitude and indifference.

In March 2026 a pump user in Switzerland went to order more Lyumjev and was told it could not be
ordered. "There's no press release, pharmacy just says they can't order it anymore due to being
discontinued," they wrote on Reddit. Lilly had told Swiss specialists the previous autumn. It had
not told the national patient organisation, which found out from a copy passed to it unofficially.

Norway lost two Lyumjev pens in October 2025, but Switzerland was the first country to lose its vial, cartridges and standard pen together. In March 2026 Lilly announced that it would stop selling selected
presentations of its insulins in selected European countries before 2027, and Lyumjev, its ultra
rapid insulin lispro, is on the list. The formal reason is "commercial". Closer to the ground, the
reason given is that not many people used it.

So Europe is losing presentations of its fastest-absorbed subcutaneous insulin after years of surprisingly
low and uneven use. The UK dispensing and formulary data in this article show that access policy is
strongly associated with that use, and that for most of the period the price of the insulin explains
very little of it. It cannot prove what drove Lilly's commercial decisions. But it raises an
uncomfortable question: did health systems help create the low-demand market that the manufacturer
is now retreating from? I think the answer is largely yes, and the rest of this article sets out
why, and where the evidence stops.

Personally, I have [used](https://www.diabettech.com/lyumjev-what-next-another-n1-experiment/) the fastest subcutaneous mealtime insulin available since each one reached
the UK, some of the time on private prescription, because I read the pharmacology and the trials and
decided that an insulin which starts working sooner was worth having. I have talked about it openly
on this website. I built Boost, the open-source automated insulin delivery algorithm I develop,
around the pharmacology of Lyumjev, and with it my own time in range (3.9 to 10 mmol/L) was about 83% between 1 April and 31 August 2026, without announcing meals or bolusing for them ([calculation](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/author_tir/RESULT.md); the personal CGM data behind it are not published). This is a
major reason for my concern.

## What is being lost

Neither Lyumjev nor Fiasp, Novo Nordisk's faster aspart, has lost its EU licence. Their
presentations (the delivery mechanism or brand name) are disappearing country by country. Lyumjev
cartridges have gone in
[France](https://www.vidal.fr/actualites/31598-insulines-lilly-en-cartouche-et-flacon-des-arrets-de-commercialisation-a-venir.html)
and Belgium, its 200 unit and Junior KwikPens in
[Norway](https://www.diabetes.no/mer/nyheter-om-diabetes/nyheter-2025/faser-ut-noen-typer-insulin/),
and its vial, cartridges and standard KwikPen in Switzerland. Germany has kept Lyumjev but [dropped
its five-pen
packs](https://www.abda.de/fuer-apotheker/arzneimittelkommission/amk-nachrichten/detail/18-26-information-der-hersteller-informationsschreiben-zu-diversen-insulin-haltigen-arzneimitteln-der-lilly-deutschland-gmbh/).
The Lyumjev Tempo Pen was [removed from the EU
licence](https://www.ema.europa.eu/en/documents/procedural-steps-after/lyumjev-epar-procedural-steps-taken-scientific-information-after-authorisation_en.pdf)
in July 2026. On the Novo Nordisk side, the Fiasp PumpCart, a prefilled cartridge for the YpsoPump,
is [being
withdrawn](https://www.ema.europa.eu/en/medicines/human/shortages/fiasp-pumpcart-insulin-aspart)
across the whole EU by the end of 2026.

The official statements are brief. The [European Medicines
Agency](https://www.ema.europa.eu/en/medicines/human/shortages/eli-lilly-insulin-various-forms-supply-shortage)
says Lilly "decided to stop marketing some of its insulin medicines for commercial reasons", and
that the decision "is not related to a quality defect or safety issue". Lilly's [template
letter](https://www.ema.europa.eu/en/documents/other/medicine-shortage-communication-msc-insulin-human-insulin-various-short-rapid-intermediate-mixed-long-acting-forms-2026_en.pdf)
to European clinicians says the decision followed "careful consideration and a thorough market
assessment". In France, Lilly said it was rationalising its insulin range worldwide to "maintain a
continuous and reliable supply of the insulins most commonly used by patients".

Digging deeper, the reason becomes specific. Norway's diabetes association, reporting the loss of
the two Lyumjev pens there, wrote that Lilly "points out that these are variants that are little
used". In Switzerland, the patient organisation diabetesschweiz complained, and in March 2026, in an
email reply that the recipient later posted publicly, passed on what it had been told, which it was
careful to call unofficial: that very few people in Switzerland had stayed on Lyumjev long term,
partly because of pain or burning at injection, and that specialist prescribing had been very low.

The UK has not seen any announcement. The NHS medicines dictionary marks only the Lyumjev Tempo
Pen as discontinued, and Lilly's March notice covers the EU and EEA. The UK's share of Lyumjev is
the same as France's, which has already lost the cartridges, and Lilly has not said what it plans
here.

## Why Lyumjev matters

Every injected rapid-acting insulin has the same problem. Food starts raising glucose within
minutes, and an injected insulin takes a good deal longer to get going. That is why we are told to
inject 15 to 20 minutes before eating and many choose to do so considerably earlier than that. In
practice many people do not wait. A [Spanish study](https://doi.org/10.3390/biomedicines12071600)
using connected pen caps recorded 775 evenings from 49 people, and in 52.6% of them (408 evenings) the dinner insulin went in up to 45 minutes after the start of the meal, as detected from the glucose trace.

The ultra-rapid insulins change the first half hour. Fiasp [appears in the
blood](https://doi.org/10.1007/s40262-017-0514-8) about five minutes earlier than NovoRapid. Lyumjev
adds citrate and treprostinil to lispro, which open up the local blood vessels, and has [several
times](https://doi.org/10.1007/s40262-021-01030-0) Humalog's exposure in the first quarter of an
hour and is typically faster still than Fiasp. In the meal test of [PRONTO-T1D](https://doi.org/10.1111/dom.14100), the rise in glucose an hour after eating was 1.55 mmol/L lower with Lyumjev than with Humalog, and a [meta-analysis](https://doi.org/10.1111/dom.14461) pooled reductions of 0.94 mmol/L in type 1 diabetes and 0.56 mmol/L in type 2, with little difference in HbA1c.

Lyumjev is the faster of the two. In a [crossover study of all four
insulins](https://doi.org/10.1111/dom.14094), it reached half its early peak concentration six minutes before Fiasp, though its lower glucose after the meal against Fiasp, about 0.4 mmol/L at two hours, was numerical and not statistically significant. In closed-loop systems the gains from both are modest and depend on the
algorithm. In the Cambridge CamAPS FX system, Fiasp [added no time in
range](https://doi.org/10.1111/dom.14355) over standard aspart (though it reduced time below range),
while Lyumjev [added 2.5 percentage points](https://doi.org/10.1089/dia.2023.0262) over standard
lispro, and a [pooled analysis of meals](https://doi.org/10.1089/dia.2023.0509) found Lyumjev
improved the four hours after breakfast where Fiasp made no measurable difference. In Medtronic
systems, Fiasp added about 1.8 to 1.9 percentage points of time in range in two studies
([670G](https://doi.org/10.1089/dia.2020.0500), [advanced hybrid closed
loop](https://doi.org/10.2337/dc21-0814)).

What people value is not having to wait. "Lyumjev is faster for me, I don't pre-bolus now and I just
feel much more confident with it," wrote a Diabetes UK forum member in 2021. A Swiss pump user wrote
in 2026 that "Lyumjev worked extremely well with Control-IQ because of the faster pharmacokinetics.
It noticeably improved post-meal spikes compared with standard lispro."

It does not suit everyone. Site pain is a common complaint, especially on pumps. In the Lyumjev
[pump trial](https://doi.org/10.1111/dom.14368), infusion-site reactions occurred in 19.1% of people
against 6.9% on Humalog, and of 29 people whose earlier public accounts I collected to illustrate experience, not to measure it, nine described pain or site reactions, seven of them with Lyumjev. "Burning, painful infusion sites that left lumps
several days after," one t:slim user wrote in March 2026. That is a reason to offer a choice:
Lyumjev suits some people and hurts others.

## Low prescribing rates

The figures that follow are shares of insulin units dispensed in the community, from England's [open
prescribing data](https://opendata.nhsbsa.net) and the equivalents for Scotland, Wales and Northern
Ireland. They count insulin supplied. They do not count people, and they cannot show who was offered
what. I suspect that far fewer people have ever been offered Lyumjev because I suspect that many clinicians don't know enough about it. I have taken the data for the UK as an example because it is freely available and extremely detailed, where other countries are less so. I suspect the same arguments apply across national boundaries.

The UK was always going to struggle with this, as by far the most frequently prescribed rapid acting
insulin comes from Novo (even though pricing for Novo and Lilly products has historically been
similar) so it would have required a major marketing push to get Lyumjev in front of prescribers. In
the year to July 2026, Lyumjev was 3.7% of the rapid-acting analogue insulin units dispensed in
English primary care, six years after it arrived. Its share of lispro has grown every year, to 24%
in 2026. Fiasp adds 13.9%, so the two ultra-rapid insulins together are 17.5% of units. It's notable
that Fiasp is still a larger share than Humalog. Other European markets split differently. In France in 2025 Humalog was 27.3% of rapid-acting analogue units and Fiasp 11.1%; in Denmark, Novo Nordisk's home market, Fiasp was 11.0% and Humalog 1.1%. Standard-speed products make up the other 82.5% of units in English primary care, about 2.74 million prescription items a year.

![Share of rapid-acting analogue units dispensed in English primary care by product, three-month rolling, January 2014 to July 2026. The black line is the combined ultra-rapid share.](fig1_share_by_product.png)

The share varies widely by paying entity (the integrated care boards). Between English integrated
care boards it ranges from 3.2% in Birmingham and Solihull to 30.0% in Leicester, Leicestershire and
Rutland. Across the UK nations it is 14.7% in Scotland, 17.4% in England, 26.4% in Northern Ireland
and 32.8% in Wales, and in one Welsh health board, Cwm Taf Morgannwg, it is 56.3%. Lyumjev alone is
6.0% of units in both Wales and Northern Ireland, against 3.7% in England and 3.4% in Scotland.

![Ultra-rapid share of rapid-acting analogue units by integrated care board, August 2025 to July 2026.](fig2_icb.png)

England is not unusual internationally. France was at 14.3% in the year to June 2026 and Denmark at
11.0% in 2025; both rose faster than England at first and then levelled off at around 11% to 15%.
The spread inside the UK is wider than the spread between countries, which points to local factors.

![Ultra-rapid share of rapid-acting analogue insulin by calendar year. Left: the four UK nations. Right: England against France, Denmark and Australia, with the German range shaded.](fig4_nations_countries.png)

## The system's part

### The trials and the guidelines

The phase 3 treat-to-target trials that supported licensing, such as [onset
1](https://doi.org/10.2337/dc16-1771) and [PRONTO-T1D](https://doi.org/10.1111/dom.14100), used
HbA1c non-inferiority as their main efficacy outcome. They all met it, and the post-meal benefit
appeared as a secondary result. Other studies have used post-meal glucose or time in range as their
main outcome, but it is the licensing programmes that guidance and formulary committees lean on, and
their headline is "no different on HbA1c". HbA1c is also what audits and incentive schemes look at,
so that headline gave a busy clinician little prompt to switch anyone.

[NICE's guidance](https://www.nice.org.uk/guidance/ng17) for adults with type 1 diabetes recommends
rapid-acting analogues as a class and names no product. Its wording on mealtime insulin dates from
2015; NICE reviewed the guideline in January 2026 and decided not to update it. The guidance does
say that if someone has a strong preference for an alternative mealtime insulin, clinicians should
respect it and offer it, which gives anyone who asks a route. It does not tell prescribers that the
faster insulins are worth raising with people who do not ask about them.

### Formularies

Each area has a formulary that sets which insulins are first choice. I read the entries for Lyumjev
in 38 areas across the UK: 17 English integrated care boards, 13 Scottish health boards, all seven
Welsh health boards and Northern Ireland. Lyumjev was open to any prescriber in five of them. In
eight it needed a specialist or set clinical criteria. In twelve it was placed behind another
insulin, as a second or third choice or only after the standard insulin had failed. In thirteen it
was not on the formulary at all, including eight of the thirteen Scottish boards and Northern
Ireland.

Some of those gaps were made by the process. From October 2020 the [Scottish Medicines
Consortium](https://www.scottishmedicines.org.uk/media/5429/guidance-on-medicines-outwith-smc-remit-october-2020.pdf)
stopped requiring a submission for "an alternative formulation of an established medicine ... which
costs the same per patient or less", which Lyumjev is, so there is no Scottish advice on it at all.
The [All Wales Medicines Strategy
Group](https://awttc.nhs.wales/accessing-medicines/medicine-recommendations/insulin-lispro-liumjev/)
excluded Lyumjev from appraisal on the same grounds, as it had Fiasp. [Northern
Ireland](https://niformulary.hscni.net/managed-entry/policy-context/) adopts NICE decisions first,
then the Scottish Consortium's, then the Welsh group's, and none of them had made one, so there was no recommendation for Northern Ireland to adopt through its usual sequence. Clinicians there can still prescribe outside the formulary or ask for an addition. A rule meant to spare same-priced medicines
unnecessary paperwork left one with no decision anywhere, and no public record shows anyone, Lilly
included, trying to close the gap.

Formulary restriction is associated with lower use. In England, where formularies left both
ultra-rapid insulins open, the median ultra-rapid share was 26.8%; where they were second line,
restricted to pregnancy or not listed, it was 9.5%. Birmingham and Solihull, the lowest in England,
[allows Fiasp only in
pregnancy](https://www.birminghamandsurroundsformulary.nhs.uk/docs/ESCA/BSSE%20APC%20ESCA%20Fiasp%20FINAL.pdf)
"after other insulins have been tried and failed" and does not list Lyumjev. Scotland shows the same
direction: the two boards using the Highland Formulary, which lists both products without
restriction, are at 26.2% and 23.5%, while the rest have a median of 5.2%. Across the 16 English integrated care boards, the rank correlation between how restrictive the formulary is and ultra-rapid use was -0.72 (95% interval -0.91 to -0.35; permutation p = 0.002), and across Scotland's 13 boards -0.51.

Taken on its own, Lyumjev tells a narrower story. The more restrictive the formulary is about Lyumjev, the less of it is used, in England and across the UK ([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/output/formulary/LYUMJEV_SUMMARY.md)). Almost all of that comes from being left off. Where Lyumjev is not listed, its median share of lispro is 5.2% in England and 2.9% in Scotland; wherever English formularies list it, under any restriction, the median is 27% to 31%, with no clear gradient between the restrictions. Leaving it off the formulary goes with very low use. Putting it behind Humalog does not show up in these numbers.

This is an association between areas, and it does not demonstrate cause, but it is highly
coincidental. The open group in England is only two integrated care boards; I classified the
formularies myself after seeing the uptake figures; many formulary pages carry no date, so current
wording is being compared with past prescribing; and none of it is adjusted for how many people use
pumps, the reach of specialist centres, the local population or past habit. Wales goes the other way: its boards that require a specialist have higher uptake than its open ones (rank correlation +0.63), so formulary position explains part of the pattern in England and Scotland and plainly not in Wales. Northern Ireland dispenses Lyumjev at 1.6 times the English rate without listing it. Local specialist practice clearly matters as well.
But a formulary that leaves an insulin off, or puts it behind the one most people are already on,
makes it harder to prescribe.

### The insulin that got through

Tresiba (insulin degludec), Novo Nordisk's ultra-long-acting insulin, is a useful comparison: a
newer insulin that the same formularies did make room for. It also costs more than the insulins it
would replace: £3.11 per 100 units at list price in English primary care in the year to July 2026,
against £2.32 for Lantus and £2.00 for Semglee, the cheapest glargine biosimilar, which has been
dispensed in England since 2019
([prices](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/output/basal/PRICES.md)).
Formularies made room for Tresiba with a cheaper long-acting insulin to protect. The ultra-rapid
insulins were in that position only after Trurapi arrived in 2021, and before then they cost no more
than the insulins they would replace.

I read the same 38 formularies for Tresiba, using the same documents and the same four categories as
for Lyumjev. Tresiba is on 37 of them and Lyumjev on 25. Of the 13 areas that leave Lyumjev off, 12
list Tresiba, Northern Ireland and seven Scottish boards among them. Tresiba is the less restricted
of the two in 20 areas and Lyumjev in 3; in the other 15 they are treated alike
([table](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/output/formulary/TRESIBA_VS_LYUMJEV.md)).
Tresiba is seldom open to any prescriber either. Most formularies tie it to a specialist or to named
uses, such as night-time hypoglycaemia or a carer giving the injection. What it has, almost
everywhere, is a written place.

![Formulary position of Lyumjev and Tresiba in 38 UK formulary areas, read in September and October 2026. Each area is counted once for each insulin.](fig5_tresiba_vs_lyumjev_formulary.png)

Part of the difference is process. As a new molecule, Tresiba had to be appraised. The [Scottish
Medicines
Consortium](https://www.scottishmedicines.org.uk/medicines-advice/insulin-degludec-tresiba-resubmission-85613/)
accepted it for use in NHS Scotland in August 2016, and the All Wales Medicines Strategy Group
recommended it in 2016 and again in 2022, so every board had a decision to adopt. Lyumjev, as a
same-priced version of an existing insulin, was spared appraisal and was given no decision at all.

Part is the kind of evidence each had. Tresiba was tested in trials whose main outcome was
hypoglycaemia: in [SWITCH 1](https://doi.org/10.1001/jama.2017.7115), people with type 1 diabetes
had fewer episodes on degludec than on glargine. When NICE revised its type 1 guidance on
long-acting insulin in 2021, it named degludec for people with "a particular concern about nocturnal
hypoglycaemia". Its mealtime recommendations still date from 2015 and name no product. A committee
could point to a problem Tresiba addressed and a group of people to give it to. For the ultra-rapid
insulins the headline was no difference in HbA1c, and the problem they address, waiting before a
meal, is not one formularies record.

The dispensing follows a similar course. Counted from launch, Tresiba was taken up in England no
faster than Fiasp for five years: 7.8% of long-acting analogue units at five years, against 7.9% of
rapid-acting units for Fiasp. They separated after the 2017 hypoglycaemia trials, and at nine years
Tresiba was at 19.6% and Fiasp at 13.9%. Areas that use more Tresiba and Toujeo also tend to use
more ultra-rapid insulin (Spearman 0.49, 95% interval 0.25 to 0.67, across 59 UK areas), so local
habit plays a part. Tresiba still reached places the faster mealtime insulins did not. Most
long-acting insulin in primary care goes to people with type 2 diabetes, so these are not the same
patients, and the timing fits the trials without showing that they caused the rise.

Abroad the route differs, and appraisal can shut a door as well as open one. France's assessment
committee re-rated Tresiba in 2019 as a minor improvement over glargine (ASMR IV) for people at high
risk of hypoglycaemia, on the strength of those trials, while it rated
[Fiasp](https://www.has-sante.fr/jcms/c_2788573) and [Lyumjev](https://www.has-sante.fr/jcms/p_3190312) as no improvement (ASMR V). In Germany
every benefit assessment of degludec found no added benefit, and
[Novo Nordisk took Tresiba off the market](https://www.deutsche-apotheker-zeitung.de/news/artikel/2015/12/16/endgultiges-aus-fur-tresiba)
from January 2016 until December 2018. Australia's
[PBAC rejected it](https://www.pbs.gov.au/industry/pbac/psd/2013/03/insulin-psd-032013.pdf) in
2013, and it was subsidised only from July 2026, while Fiasp was listed there by the end of 2019 at
the same price as NovoRapid. Outside Australia, wherever both can be measured, Tresiba now takes a larger share of
long-acting insulin than the ultra-rapid insulins take of rapid-acting: 22% against 15% in France in
2025, 41% against 11% in Denmark, and 20% against 9% in the US Medicare drug programme in 2024
([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/international/output/BASAL_INTL.md)).
Price parity for the faster insulins was also a mostly British arrangement. In France Fiasp is listed
at €2.09 per 100 units against €1.48 for NovoRapid, and in Denmark at 32.1 kroner against 16.7.
Denmark's reimbursement committee counted Fiasp among "de dyrere lægemidler" (the more expensive
medicines) in 2019, and since 2022 it has been reimbursed only for people whose after-meal glucose is
not managed on another rapid insulin.

![Degludec (Tresiba) as a share of long-acting analogue insulin against the ultra-rapid share of rapid-acting analogue insulin, latest year available. Germany's ultra-rapid share is a range because its data pool Lyumjev with Liprolog; Australia counts PBS prescriptions, and degludec was not subsidised there until July 2026.](fig6_degludec_vs_ultra_countries.png)

### Cost before biosimilars

For much of the period, the price of the insulin offers little explanation. Lyumjev has cost English
primary care the same per unit as Humalog in every year since it arrived. Its list price per box is
the same as Humalog's. Fiasp was the same against NovoRapid. For the 52 months between Fiasp's arrival in February 2017 and the first biosimilar, Trurapi, in June 2021, English primary care paid £1.68 per 100 units of Fiasp against £1.76 for NovoRapid. There was little or no acquisition-cost premium for choosing the faster formulation. That is not the same as no cost to the system:
switching takes clinic time and training, and pumps and pens have to be compatible. Those costs are
not measured here.

In those 52 months, 10.1 million prescription items for standard-speed rapid-acting insulin were
dispensed in England, more than 97 of every 100 rapid-acting analogue items. Some of that was
formulary committees keeping the faster insulins out. North Central London recorded Fiasp as "Not
approved for: Adults with Type 1 diabetes" in November 2018. Birmingham and Solihull restricted it
to pregnancy in June 2019. South East London made it a second-line option in January 2020. None of
those decisions could have rested on the acquisition price.

It was not only committees. In June 2017, four months after Fiasp arrived, people on the
[diabetes.co.uk forum](https://www.diabetes.co.uk/forum/threads/fiasp-experiences.121804/) were
describing what happened when they asked for it. One was given "a straight 'No'" by a diabetes
consultant: "Apparently I am too well controlled to change anything!" A pump user was told "no your
a1c is low enough as it is, we don't want it going any lower!!" and got it only after arguing.
Another had been told by a consultant and a specialist nurse that Fiasp "is still undergoing trials,
and is not available on their formulary", and after three or four attempts had got nowhere. A
specialist nurse told another that their clinic would move only NovoRapid users across, because
"they don't think there is much difference between Humalog and Fiasp". I wrote in the same thread at
the time that "Many HCPs will not prescribe it until they see the outcome of this trial because they
don't want to get in to trouble for prescribing something they don't have details of."

People told me at the time that some consultants in England went further and said they did not
believe a faster insulin offered any benefit, and would not therefore prescribe Fiasp. These were
clinical judgements made against the trials' own meal-test results and against what the people
asking for it were saying. At around the same time, the feedback received at a major diabetes
conference from one of the manufacturer reps was that the prescribing committee doesn’t want anyone
on novel insulins because they can’t easily transition them to biosimilars.

These data cannot show how often anyone was offered a faster insulin and declined it, perhaps
because of site pain. As I've already mentioned, I'm reasonably sure that large swathes of the
population simply weren't offered it. Among the small number of hospital prescriptions dispensed in the community, 0.13% of rapid-acting units, the ultra-rapid share is about twice the GP figure (35.6% against 17.6% on the same six-brand basis), yet most of it is still standard-speed. The much larger supply issued inside hospitals cannot be split by brand. What the data do show is that, through the years when the faster insulins carried
little or no price premium, they stayed at under 6% of the rapid-acting insulin dispensed in
England.

### Cost after biosimilars

From 2021 there was a cheaper insulin to protect. Trurapi and the other biosimilars are about 30%
cheaper than NovoRapid and work at the same speed. [Norfolk and
Waveney](https://nwknowledgenow.nhs.uk/wp-content/uploads/2025/09/Trurapi-2025-Guidance-v1.1-Sept-2025.pdf)
estimated that moving 80% of people from NovoRapid to Trurapi would save about £340,000 a year, and
[Cheshire and
Merseyside](https://www.cheshireandmerseysideformulary.nhs.uk/docs/files/trurapi_position.pdf) about
£1 million. Each is about an eighth of what the area now spends on rapid-acting analogues at list
price. NHS Dorset's [2026/27 prescribing incentive
scheme](https://nhsdorset.nhs.uk/medicines/value/insulin-aspart/) asks primary care networks to make
biosimilar aspart at least half of all aspart prescribing. Those documents exclude Fiasp from the
switch, but once Trurapi is first choice an ultra-rapid insulin becomes a second step, and the trial
evidence gives that step little to stand on. Trurapi reached 7.5% of units within five years.
Lyumjev, after six, is at 3.7%.

Outside England, biosimilars don't explain the low use of the faster insulins. In Denmark and
Germany they were about 5% of rapid-acting analogue insulin in 2025, and in France 2.9%. The
discount on NovoRapid in France and Denmark is only 4 to 5%, and in each country the faster insulins
held at 11% to 15%. In the US Medicare drug programme Admelog costs the same as Humalog. England is
where that could change. Trurapi lists at 21% less than NovoRapid overall and 30% less for pens. Its
share of rapid-acting units rose from 0.3% in 2022 to 6.0% in 2025, pushed by incentive schemes such
as Dorset's and by formularies such as North West London's that send every new start to it. Within
the UK, the two nations with the most ultra-rapid use, Wales at 30.9% and Northern Ireland at 23.9%,
dispensed almost no biosimilar: 2.1% in Wales and none at all in Northern Ireland. The concern is
that once England makes the cheaper standard-speed insulin the default for new starters, the people
who might have done better on a faster insulin are never offered one, and the gap with Wales grows
([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/international/output/RAPID_BIOSIMILAR_INTL.md)).

### Where the savings should come from

The biosimilar effort has been pointed at the wrong insulin. In the year to July 2026, at list price
and device for device, Fiasp cost English primary care exactly what NovoRapid cost, and Lyumjev exactly
what Humalog cost. Moving someone from either older insulin to its faster version adds no acquisition cost at published list prices for the same device; the clinic time a switch takes is a separate cost. The
only money at stake is the saving given up by not moving them to Trurapi, which is £0.47 per 100 units
cheaper than Fiasp. Lispro has no cheaper alternative left to protect, since Sanofi is withdrawing
Admelog.

Long-acting insulin is where a switch does not mean accepting a slower insulin, though it is still a shared decision and a new pen to learn. Semglee, the cheapest glargine,
lists at £2.00 per 100 units against £2.32 for Lantus and £2.35 for Abasaglar, the older biosimilar,
and it is the same molecule with the same profile of action. Yet it is 4.8% of the glargine 100
dispensed in England. Moving 80% of Lantus and Abasaglar pens to it would save about £5.5 million a
year. That is enough to pay for 14.5% of all the rapid-acting insulin dispensed in England to be Fiasp
in place of Trurapi, and close to the £5.8 million, at most, that bringing England up to Wales's
ultra-rapid share would forgo
([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/output/biosimilar/SUMMARY.md)).

North West London shows the blunt version. Its formulary says "All new initiations should be the lower
cost biosimilar, Trurapi, instead of NovoRapid". It leaves Fiasp off and makes Lyumjev a second-line
choice for specialists to start. For long-acting insulin it lists Lantus, Abasaglar and Semglee side by
side, with no preference for the cheapest. Its ultra-rapid share is 10.1%, the 12th lowest of 106
areas in England. Even the biosimilar push has gone slowly there: Trurapi is 9.2% of its standard
aspart and Semglee 5.1% of its glargine.
Moving 80% of its glargine pens to Semglee would save about £300,000 a year, more than the £270,000 it
would give up in reaching Wales's ultra-rapid share. A more granular policy, pressing the biosimilar
where speed is not at stake and leaving the faster mealtime insulins open to anyone who wants them,
would have saved money and widened choice at the same time.

![Annual figures at list price, August 2025 to July 2026. The first two bars are the savings from moving 80% of Lantus and Abasaglar pens to Semglee and 80% of NovoRapid to Trurapi. The third is the most it would cost, in Trurapi savings given up, to reach Wales's ultra-rapid share.](fig7_biosimilar_savings.png)

These are list prices, which leave out confidential discounts, and they keep everyone on the same
kind of device. Semglee is sold only as a pen, so the 230 million units of Lantus and Abasaglar in
cartridges are left out.

### Lilly's part

Lilly's role in this needs to be questioned too. On the public record, it did the formal work each
country required, and I found little public evidence of a sustained campaign in the UK beyond it.

In France, Lilly applied for reimbursement and, according to the [assessment committee's transcript](https://www.has-sante.fr/upload/docs/application/pdf/2020-07/lyumjev_03062020_transcription_ct18474.pdf), claimed no added benefit over Humalog ("pas d'ASMR"), presenting the trials' comparable HbA1c and better post-meal glucose. The committee rated Lyumjev ASMR V, no improvement over Humalog, noting no demonstrated advantage in efficacy, tolerance or quality of
life. In Germany Lilly agreed [rebate
contracts](https://www.g-ba.de/downloads/40-268-12140/2025-12-04_AM-RL_Paragraf-40-c_Austausch-Biologika-Apotheke_ZD.pdf)
covering Humalog, Lyumjev and Abasaglar for "nearly all" people with statutory insurance.

When Fiasp reached the UK in April 2017, it was
[reported](https://www.diabetes.co.uk/news/2017/apr/new-faster-acting-insulin-fiasp-now-available-in-the-uk-97369705.html)
as "made available to the NHS at no additional cost compared to NovoRapid". I found no comparable UK
announcement for Lyumjev in 2020, in the diabetes press or from Lilly. Lilly was a named
collaborator on Tandem and Medtronic trials that led to US clearances of Lyumjev with Tandem's
t:slim X2 in 2025 and with Medtronic's MiniMed 780G in [December
2025](https://www.prnewswire.com/news-releases/medtronic-diabetes-expands-access-to-full-stack-insulin-delivery-solutions-with-medicare-access-and-new-fda-clearances-302676383.html);
every site in both trials was in the United States. In the UK, Medtronic's [780G
page](https://www.medtronic-diabetes.co.uk/insulin-pump-therapy/minimed-780g-system) still lists
"Humalog and NovoRapid" only, and [Omnipod 5](https://www.omnipod.com/en-gb/safety) lists neither
ultra-rapid insulin. Tandem's UK and European t:slim X2 guide does list Lyumjev.

Lilly priced Lyumjev the same as Humalog, which removed the most obvious barrier, and several of the
obstacles above applied to Novo Nordisk's Fiasp just the same. Lilly's field activity, medical
education and dealings with payers are not public, so I cannot say how much it did. What I can say
is that I found little public sign of a case being made for Lyumjev in the UK, and that in Norway
Lilly has described the presentations it is withdrawing as little used.

## What "commercial reasons" means in money

These are what payers spent at list or reimbursement prices, and they give a sense of scale. In England,
primary care spent £5.6 million on Lyumjev in the year to July 2026, against £18.3 million on
Humalog. In France it was €6.4 million against €49.3 million. In the US Medicare drug programme
Lyumjev took $90 million in 2024, against $664 million for Humalog. Lyumjev is between a tenth and a
quarter of what payers spent on Lilly's rapid-acting insulins in each of these markets
([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/international/output/COMMERCIAL.md)).

Pricing every market at the NHS list price, the figure the BNF prints, puts them on one scale. On
that basis the UK's rapid-acting analogue market came to £174 million over the latest twelve months:
£143 million in England, £16 million in Scotland, £9.1 million in Wales and £6.0 million in Northern
Ireland. Lyumjev was £7.1 million of it (4.1%) and Fiasp £24.6 million. France's 2025 community
dispensing would cost £170 million at the same prices, with Lyumjev £6.1 million of it. Germany's
statutory-insurance market would cost £218 million, and there Lyumjev is pooled with Liprolog in a
line worth £34 million. Local prices differ from the NHS's, so these are volumes priced in pounds
and say nothing about what each country paid
([figures](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/international/output/MARKET_VALUE.md)).

For context, Lilly's total revenue in the first three months of 2026 was [$19.8
billion](https://www.sec.gov/Archives/edgar/data/0000059478/000005947826000045/lly-20260331.htm),
$12.8 billion of it from Mounjaro and Zepbound, which in 2025 [accounted for
56%](https://www.annualreports.com/HostedData/AnnualReports/PDF/NYSE_LLY_2025.pdf) of its revenue.
That contrast does not show that Lilly moved money or attention from insulin to its newer products;
the European Medicines Agency records only that the reasons were commercial. It does show how small
a line Lyumjev is in each European market.

## What the community is saying

I collected 31 public posts from people with diabetes across Europe, and 11 statements from companies, regulators and patient groups, from 2025 and 2026. The posts were gathered to show the range of reactions. They are not a sample, so they say nothing about how common any view is.

The sharpest reaction is from Switzerland, where Lyumjev's main presentations went first. "Not cool that the best insulin
for tslim gets discontinued by the manufacturer - also without any sort of proper announcement"
(Reddit, Switzerland, March 2026). "Why was my favorite insulin (Lyumjev) pulled from the Swiss
market?" (Reddit, Switzerland, April 2026). "I am from Switzerland and currently use my very last
Lyumjev pen" (Reddit, July 2026).

Some suspect insulin is being sidelined for weight-loss drugs, which is speculation the evidence
above can't confirm: "Lyumjev is handsdown the best insulin on the market at this time, its a shame
Eli Lilly wants to take it away from many people so they can focus on more profitable endeavours
such as Mounjaro" (Reddit, May 2026). Another person wrote: "It's such a quality of life issue"
(Reddit, September 2026). In the UK the mood is uncertainty: "Doesn't look like they've said
anything about withdrawing Lyumjev in the UK, just EU/EEA, so hopefully they keep it here, but does
seem worrying" (Reddit, UK, July 2026).

Not everyone is sorry. The site pain comes up again, and Norway's diabetes association quoted a
professor saying there are good alternatives to every insulin being withdrawn there. In the Czech
Republic, where Lilly said supplies were continuing, the national regulator
[reported](https://www.vitalia.cz/clanky/problemy-s-inzulinem-do-pump-lyumjev-chybi-v-lekarnach/) in
July 2025 that Lyumjev deliveries had risen by 20% in a year, driven by pump users including
children.

## What comes next?

As algorithms are asked to handle meals without being told about them, the speed of the insulin
matters more. A fully closed loop has to catch a meal from the glucose rise alone, and the faster
its insulin acts the less of the rise it misses. The manufacturers are moving that way. In May 2026
Insulet [enrolled the first
participant](https://investors.insulet.com/news/news-details/2026/Insulet-Initiates-EVOLVE-Pivotal-Study-to-Advance-Fully-Closed-Loop-Automated-Insulin-Delivery-System-for-Type-2-Diabetes/default.aspx)
in EVOLVE, a pivotal randomised trial of up to 350 adults at 40 US sites, of a fully closed-loop
system for type 2 diabetes that it says eliminates "user interactions for bolusing and mealtime
announcements". In June 2026 MiniMed
[said](https://www.medtechdive.com/news/minimed-is-in-the-lead-as-diabetes-tech-firms-focus-on-fully-closed-loop/822446/)
it was about halfway through enrolling a pivotal trial of an algorithm, for type 1 as well as type 2
diabetes, that "would remove the need for pre-meal insulin doses"; in its early testing, people
spent 82% of the time in range when they announced meals and about 74% when they did not. Neither
company has said which insulin its system is designed around.

Fully closed loop works with the insulins already available. Cambridge's CamAPS HX has run it with
Fiasp in [adults with type 2 diabetes](https://doi.org/10.1038/s41591-022-02144-z) and in
[adolescents with type 1 diabetes](https://doi.org/10.1089/dia.2025.0062), and with Lyumjev in
[adults with type 1 diabetes](https://doi.org/10.1089/dia.2023.0394). The one trial comparing
Lyumjev with standard lispro in fully closed loop with unannounced meals found time in range of 49.3% against 39.9% in 17 people, over 8-hour inpatient sessions with one unannounced meal, a difference that did not reach statistical significance ([p =
0.072](https://doi.org/10.1111/dme.70122)). Its authors concluded that "Further advancements in
faster-acting insulins are needed to alleviate the burden of pre-meal bolusing and enhance fully
closed-loop performance in the future." As one person put it in September 2026: "every minute counts
with a system working on a time offset."

So fully closed loop does not depend on Lyumjev. The 9.4-point difference in that trial would matter to someone living with it, but it came from a small, short study and was too imprecisely estimated to reach statistical significance. Insulin speed is still one of the few ways of reducing the delay these systems have to work around, and in Europe the fastest-absorbed subcutaneous insulin is being withdrawn country by country, with low use given as the reason by Lilly in Norway and, in the patient organisation's unofficial account, in Switzerland. Pump users can still fill reservoirs from Fiasp vials, as the
German Diabetes Society has pointed out, but the options are narrowing as the systems that would
benefit most arrive. The UK still has every Lyumjev presentation except the Tempo Pen.

## Where do we go from here?

None of the reasons Lyumjev was so little used rests on evidence that the older insulins are better.
They have, by default, been left in place: licensing trials built around equivalence on the measure
everyone watches, guidance that names no product, formularies that left Lyumjev off altogether in a third of the UK areas I read, cost programmes that made a cheaper standard-speed insulin first choice
once there was one, and a manufacturer that made little visible case for it.

The part I find hardest to accept is the years before biosimilars. The faster insulins carried
little or no price premium over the ones they would have replaced, and they stayed at under 6% of
the rapid-acting insulin dispensed in England. Some people who asked for them in that period were
refused. I cannot measure from these data how many others might have chosen them if offered, but the
quality-of-life case was there from the start and the system did not act on it. The low use that
followed is now part of the background to the withdrawals.

Wales shows it did not have to go this way. Across a whole nation a third of rapid-acting insulin
dispensed is ultra-rapid, and in one health board more than half.

What I want to see now is the diabetes charities and patient organisations of Europe standing up and
being counted, and so far they have barely made a sound. Diabetes UK's page on insulin supply lists
ten discontinuations and shortages and does not mention Lyumjev or the withdrawals across Europe, and
Breakthrough T1D UK's site mentions Lyumjev only in its guide to connected pens. In France, which has
already lost the cartridges, the last thing I can find on Lyumjev from the national federation of
people with diabetes is a 2023 note about a temporary shortage. Germany's diabetesDE has nothing on
it, and the German Diabetes Society's statement was practical advice on pump cartridge shortages
([search record](https://github.com/tim2000s/rapid-insulin-prescribing/blob/master/withdrawals_eu/charities/SEARCH_LOG.md)).
Norway's diabetes association
reported the withdrawals and quoted a professor reassuring readers that there were good alternatives
to every insulin going. diabetesschweiz complained to Lilly, then passed on its own unofficial account of what it had been told: that hardly anyone used it. Reporting a withdrawal and relaying the manufacturer's reasons is the least an
organisation can do, and these organisations exist to speak for the people who use these insulins.
They should be demanding that the faster insulins stay on the market, that they are part of the fully
closed-loop systems now in trials, that formularies stop parking them behind the insulin people are
already on, and that clinicians offer them to everyone who might benefit and let each person decide
for themselves whether to turn them down. When they stay quiet, the manufacturer's account of low
demand is the only one anyone hears.

Is this a failure of the system? Yes, at every level, and nobody escapes the blame. The licensing
trials were built to show the new insulins were no worse on HbA1c, and that was read as showing they
were no better. NICE left its mealtime insulin advice as it stood in 2015, looked at it again in
January 2026 and left it there. The Scottish and Welsh appraisal bodies wrote rules that left Lyumjev
without a decision in either country, and Northern Ireland, which depends on them, inherited the gap.
Formulary committees left it off in 13 of 38 areas, which is where its use is lowest, while
finding a written place for Tresiba, which costs a third more than Lantus. Consultants told people who
asked for a faster insulin that they were too well controlled to need one. Lilly priced Lyumjev the
same as Humalog and then, as far as the public record shows, did almost nothing to make the case for
it in the UK, and did not even tell the Swiss patient organisation that it was going. The charities,
whose whole purpose is to make noise about exactly this, have barely raised their voices.

The cost of it all falls on people with diabetes who had less chance to make that choice. These data cannot show who was offered what, but they make it very hard to believe the pattern arose because almost everyone preferred the older insulins.

---

The method, the code, the formulary wording area by area and the outputs behind every number are at
https://github.com/tim2000s/rapid-insulin-prescribing. The sources follow.
