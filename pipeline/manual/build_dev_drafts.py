"""Hand-authored drafts for the dev papers (single pass, read in a Claude Code session).

Run: ../../.venv/bin/python build_dev_drafts.py ../../data/evidence/manual_drafts_dev.json
then: cd .. && ../.venv/bin/python extract.py --from-drafts ../data/evidence/manual_drafts_dev.json
(and the same for manual_drafts_dev_neuro.json, written next to it).
"""
import json
import sys

OUT = sys.argv[1]


def exp(label, design, species, pop, n, unit="participant"):
    return dict(label=label, design=design, species=species, population_or_model=pop, n=n,
                independent_unit=unit)


def arm(label, orig, norm, dose=None, dose_unit=None, route=None, regimen=None,
        comp_label=None, comp_type="baseline_within_subject"):
    return dict(label=label, intervention_original=orig, intervention_normalized=norm,
                dose_value=dose, dose_unit=dose_unit, route=route, regimen=regimen,
                comparator_label=comp_label, comparator_type=comp_type)


def meas(endpoint, scale, direction, *, norm=None, instrument=None, t=None, t_unit=None,
         t_origin=None, value=None, unit=None, control=None, es_type=None, es=None,
         unc="none_reported", lo=None, hi=None, test=None, p=None):
    return dict(endpoint_original=endpoint, endpoint_normalized=norm, scale_level=scale,
                assay_or_instrument=instrument, time_value=t, time_unit=t_unit, time_origin=t_origin,
                value=value, value_unit=unit, control_value=control, effect_direction=direction,
                effect_size_type=es_type, effect_size_value=es, uncertainty_type=unc,
                uncertainty_low=lo, uncertainty_high=hi, statistical_test=test, p_value=p,
                value_origin="author_reported")


def anchor(quote, section="Results", label=None, location="text"):
    return dict(location=location, section=section, label=label, quote=quote)


def clin(scale=None, higher=None, resp=None, remis=None, resp_def=None, blind=None, follow=None):
    return dict(scale_name=scale, higher_score_means=higher, responder_rate=resp, remission_rate=remis,
                response_definition=resp_def, blinding_integrity_assessed=blind, follow_up=follow,
                adverse_events=[])


def row(e, a, m, anchors, clinical=None, missing=()):
    return dict(experiment=e, arm=a, measurement=m, anchors=anchors, clinical=clinical,
                preclinical=None, missing=[dict(field=f, reason=r) for f, r in missing])


drafts = {}

# --- PMC5640601: psilocybin for TRD, fMRI mechanisms (open-label) -------------
E_ASL = exp("Open-label TRD trial, ASL subsample", "open_label_trial", "human",
            "adults with treatment-resistant major depression", 16)
E_ASL15 = exp("Open-label TRD trial, ASL subsample with ratings", "open_label_trial", "human",
              "adults with treatment-resistant major depression", 15)
E_BOLD = exp("Open-label TRD trial, BOLD subsample", "open_label_trial", "human",
             "adults with treatment-resistant major depression", 15)
E_ALL = exp("Open-label TRD trial, full sample", "open_label_trial", "human",
            "adults with treatment-resistant major depression", 19)
A_PSI = arm("Psilocybin (10 mg then 25 mg)", "psilocybin", "Psilocybin", 25, "mg",
            regimen="10 mg followed by 25 mg, one week apart", comp_label="pre-treatment")
QIDS = dict(scale="QIDS-SR16", higher="worse",
            resp_def="QIDS-SR16 reduction of 50% or more", blind="no")
drafts["PMC5640601"] = dict(
    reports_measured_outcomes=True,
    screening_reason="Open-label trial reporting depression scores and pre/post fMRI blood flow and connectivity.",
    measurements=[
        row(E_ASL15, A_PSI,
            meas("QIDS-SR16 depression score, day of post-treatment scan", "clinical", "decrease",
                 instrument="QIDS-SR16", t=1, t_unit="day", t_origin="25 mg dose", value=8.8,
                 unit="points", control=16.9, unc="SD", lo=6.2, test="paired t-test", p="<0.001"),
            [anchor("it was 8.8 ± 6.2 (change = −8.1 ± 6, t = −5.2, p < 0.001)")],
            clin(**QIDS, follow="1 day")),
        row(E_ASL15, A_PSI,
            meas("QIDS-SR16 depression score, 5 weeks post-treatment", "clinical", "decrease",
                 instrument="QIDS-SR16", t=5, t_unit="weeks", t_origin="treatment", value=10.9,
                 unit="points", control=18.9, unc="SD", lo=4.8, test="paired t-test", p="<0.001"),
            [anchor("for 5-weeks post-treatment, it was 10.9 ± 4.8 (change = −8 ± 5.1, t = −6.3, p < 0.001)")],
            clin(**QIDS, follow="5 weeks")),
        row(E_ALL, A_PSI,
            meas("QIDS-SR16 change from baseline, full sample, 5 weeks", "clinical", "decrease",
                 instrument="QIDS-SR16", t=5, t_unit="weeks", t_origin="treatment", value=-9.2,
                 unit="points (change)", unc="SD", lo=5.6, test="paired t-test", p="<0.001"),
            [anchor("47% met criteria for response (change = −9.2 ± 5.6, t = −6.7, p < 0.001)")],
            clin(**QIDS, resp=0.47, follow="5 weeks")),
        row(E_ALL, A_PSI,
            meas("QIDS-SR16 change from baseline, full sample, 1 week", "clinical", "decrease",
                 instrument="QIDS-SR16", t=1, t_unit="week", t_origin="treatment", value=-10.2,
                 unit="points (change)", unc="SD", lo=5.3, test="paired t-test", p="<0.001"),
            [anchor("with 12 meeting criteria for response (change = −10.2 ± 5.3, t = −6.4, p < 0.001)")],
            clin(**QIDS, follow="1 week")),
        row(E_ASL, A_PSI,
            meas("Amygdala cerebral blood flow (ASL), post vs pre", "circuit", "decrease",
                 norm="amygdala_cbf", instrument="arterial spin labelling fMRI", t=1, t_unit="day",
                 t_origin="25 mg dose", es_type="correlation", es=0.59, p="0.01"),
            [anchor("Only decreases in CBF were observed post treatment (vs pre)"),
             anchor("a significant relationship was found (r = 0.59; p = 0.01)")],
            missing=[("measurement.value", "not_reported")]),
        row(E_BOLD, A_PSI,
            meas("vmPFC to inferior-lateral parietal cortex resting-state connectivity", "circuit", "increase",
                 norm="vmpfc_ilpc_rsfc", instrument="BOLD resting-state fMRI", t=1, t_unit="day",
                 t_origin="25 mg dose"),
            [anchor("Increased vmPFC RSFC was observed with the bilateral inferior-lateral parietal cortex (ilPC) post-treatment.")],
            missing=[("measurement.value", "not_reported")]),
        row(E_BOLD, A_PSI,
            meas("Parahippocampus to prefrontal cortex resting-state connectivity", "circuit", "decrease",
                 norm="parahippocampus_pfc_rsfc", instrument="BOLD resting-state fMRI", t=1, t_unit="day",
                 t_origin="25 mg dose"),
            [anchor("Decreased PH RSFC was observed with a PFC cluster incorporating the lateral and medial prefrontal cortex.")],
            missing=[("measurement.value", "not_reported")]),
        row(E_BOLD, A_PSI,
            meas("Amygdala resting-state connectivity", "circuit", "no_change",
                 norm="amygdala_rsfc", instrument="BOLD resting-state fMRI", t=1, t_unit="day",
                 t_origin="25 mg dose"),
            [anchor("Amygdala RSFC was not significantly altered post treatment.")],
            missing=[("measurement.value", "not_reported")]),
        row(E_BOLD, A_PSI,
            meas("Default-mode network within-network connectivity (uncorrected)", "circuit", "increase",
                 norm="dmn_within_rsfc", instrument="BOLD resting-state fMRI", t=1, t_unit="day",
                 t_origin="25 mg dose", test="t-test, did not survive Bonferroni correction", p="0.018"),
            [anchor("revealed increased default-mode network (DMN) (t = 2.7, p = 0.018)")],
            missing=[("measurement.value", "not_reported")]),
    ])

# --- PMC5895707: hypothesis paper ------------------------------------------------
drafts["PMC5895707"] = dict(
    reports_measured_outcomes=False,
    screening_reason="Hypothesis article proposing a mechanism; it reports no new measurements.",
    measurements=[])

# --- PMC6617883: microdosing codebook (qualitative) ------------------------------
drafts["PMC6617883"] = dict(
    reports_measured_outcomes=False,
    screening_reason="Qualitative coding of self-reported microdosing benefits and challenges; no measured outcomes against a comparator.",
    measurements=[])

# --- PMC6047302: nature relatedness / authoritarianism after psilocybin ----------
E_TRD = exp("Open-label pilot, TRD patients", "open_label_trial", "human",
            "adults with treatment-resistant depression", 7)
E_TRD6 = exp("Open-label pilot, TRD patients (7-12 month follow-up)", "open_label_trial", "human",
             "adults with treatment-resistant depression", 6)
E_CTRL = exp("Open-label pilot, untreated healthy controls", "open_label_trial", "human",
             "age-matched healthy adults, no psilocybin", 7)
A_P2 = arm("Psilocybin (10 mg then 25 mg)", "psilocybin", "Psilocybin", 25, "mg",
           regimen="10 mg safety dose, then 25 mg one week later", comp_label="baseline")
A_NONE = arm("Healthy controls, no drug", "not administered psilocybin", "none", comp_label="screening")
NR = "NR-6 nature relatedness score"
PPQ = "PPQ-5 authoritarianism score"
drafts["PMC6047302"] = dict(
    reports_measured_outcomes=True,
    screening_reason="Open-label pilot reporting questionnaire scores before and after psilocybin with an untreated control group.",
    measurements=[
        row(E_TRD, A_P2,
            meas(NR + ", 1 week", "behavioral", "increase", instrument="Nature Relatedness Scale (NR-6)",
                 t=1, t_unit="week", t_origin="dosing sessions", value=4.14, unit="points", control=3.67,
                 es_type="standardized_mean_difference", es=2.5, unc="SD", lo=0.75,
                 test="paired t-test", p="0.003"),
            [anchor("Patients showed a significant increase in nature relatedness scores 1 week after psilocybin treatment ( M =4.14, SD =0.75) compared with baseline ( M =3.67, SD =1.00)")]),
        row(E_TRD6, A_P2,
            meas(NR + ", 7-12 months", "behavioral", "increase", instrument="Nature Relatedness Scale (NR-6)",
                 value=4.12, unit="points", control=3.67, es_type="standardized_mean_difference", es=1.2,
                 unc="SD", lo=0.60, test="paired t-test", p="0.021"),
            [anchor("the significant change was sustained at the 7–12-month follow-up time-point ( M =4.12, SD =0.60; t (5)=−2.707, p =0.021")],
            missing=[("measurement.time_value", "ambiguous")]),
        row(E_CTRL, A_NONE,
            meas(NR + ", 1 week", "behavioral", "no_change", instrument="Nature Relatedness Scale (NR-6)",
                 t=1, t_unit="week", t_origin="screening", value=4.02, unit="points", control=4.02,
                 unc="SD", lo=0.94, test="paired t-test", p="0.994"),
            [anchor("Non-treated control subjects showed no difference between screening ( M =4.02, SD =0.79) and the first ( M =4.02, SD =0.94; t (6)=0.008, p= 0.994")],
            missing=[("arm.dose_value", "not_applicable")]),
        row(E_TRD, A_P2,
            meas(PPQ + ", 1 week", "behavioral", "decrease", instrument="Political Perspective Questionnaire (PPQ-5)",
                 t=1, t_unit="week", t_origin="dosing sessions", value=2.43, unit="points", control=2.89,
                 es_type="standardized_mean_difference", es=0.8, unc="SD", lo=0.73,
                 test="paired t-test", p="0.039"),
            [anchor("Patients showed a significant decrease in authoritarian political perspective 1 week after psilocybin treatment ( M =2.43, SD =0.73) relative to baseline ( M =2.89, SD =0.72)")]),
        row(E_TRD6, A_P2,
            meas(PPQ + ", 7-12 months", "behavioral", "decrease", instrument="Political Perspective Questionnaire (PPQ-5)",
                 value=2.27, unit="points", control=2.89, es_type="standardized_mean_difference", es=0.7,
                 unc="SD", lo=0.68, test="paired t-test (trend level)", p="0.065"),
            [anchor("Decreases in authoritarianism were still evident 7–12 months post-dosing ( M =2.27, SD =0.68)")],
            missing=[("measurement.time_value", "ambiguous")]),
        row(E_TRD, A_P2,
            meas("QIDS depression score, 1 week", "clinical", "decrease", instrument="QIDS",
                 t=1, t_unit="week", t_origin="dosing sessions", value=12.29, unit="points", control=19.43,
                 es_type="standardized_mean_difference", es=1.3, unc="SD", lo=9.18,
                 test="Wilcoxon signed-rank", p="0.025"),
            [anchor("patients showed a significant decrease in QIDS scores 1 week after the psilocybin sessions ( M =12.29, SD =9.18) compared with baseline ( M =19.43, SD =4.04)")],
            clin(scale="QIDS", higher="worse", blind="no", follow="1 week")),
        row(E_TRD6, A_P2,
            meas("QIDS depression score, 7-12 months", "clinical", "decrease", instrument="QIDS",
                 value=13.00, unit="points", control=19.43, es_type="standardized_mean_difference", es=0.7,
                 unc="SD", lo=6.39, test="Wilcoxon signed-rank", p="0.038"),
            [anchor("The patients’ QIDS scores remained significantly decreased 7–12 months after psilocybin treatment ( M =13.00, SD =6.39)")],
            clin(scale="QIDS", higher="worse", blind="no", follow="7-12 months"),
            missing=[("measurement.time_value", "ambiguous")]),
    ])

# --- PMC6695371: 5-MeO-DMT toad secretion, naturalistic observational -------------
E_24 = exp("Naturalistic observational study, 24 h assessment", "observational", "human",
           "adults inhaling toad secretion at retreats in Europe", 42)
E_4W = exp("Naturalistic observational study, 4-week follow-up", "observational", "human",
           "adults inhaling toad secretion at retreats in Europe", 24)
A_TOAD = arm("Inhaled toad secretion containing 5-MeO-DMT",
             "vapor from dried toad secretion containing 5-MeO-DMT", "5-MeO-DMT",
             route="inhalation", regimen="single inhalation session", comp_label="baseline")
G = "standardized_mean_difference"
MISS_DOSE = ("arm.dose_value", "not_reported")
MISS_VAL = ("measurement.value", "not_reported")


def toad(e, endpoint, scale, direction, instrument, t, p, g, quote, clinical=None, missing=()):
    t_kw = dict(t=4, t_unit="weeks", t_origin="inhalation") if t == "4w" else {}
    miss = [MISS_DOSE, MISS_VAL, *missing]
    if t != "4w":
        miss.append(("measurement.time_value", "ambiguous"))
    return row(e, A_TOAD, meas(endpoint, scale, direction, instrument=instrument, es_type=G if g else None,
                               es=g, test="linear mixed model contrast (Bonferroni)", p=p, **t_kw),
               [anchor(quote)], clinical, miss)


DASS = dict(scale="DASS-21", higher="worse")
drafts["PMC6695371"] = dict(
    reports_measured_outcomes=True,
    screening_reason="Observational study reporting questionnaire and task outcomes before and after one inhalation session.",
    measurements=[
        toad(E_24, "Satisfaction with life, within 24 h", "behavioral", "increase", "Satisfaction with Life Scale",
             "24h", "0.022", 0.29,
             "satisfaction with life significantly increased within 24 h following the inhalation of the vapor from dried toad secretion containing 5-MeO-DMT ( p = 0.022; Hedges’ g = 0.29)"),
        toad(E_4W, "Satisfaction with life, 4 weeks", "behavioral", "increase", "Satisfaction with Life Scale",
             "4w", "0.012", 0.41, "and persisted 4 weeks later ( p = 0.012; Hedges’ g = 0.41)"),
        toad(E_24, "DASS-21 depression, anxiety and stress, within 24 h", "clinical", "decrease", "DASS-21",
             "24h", None, None,
             "subjective ratings of depression, anxiety, and stress decreased within 24 h following the inhalation of the vapor from dried toad secretion containing 5-MeO-DMT, but failed to reach significance until 4 weeks later",
             clin(**DASS)),
        toad(E_4W, "DASS-21 depression, 4 weeks", "clinical", "decrease", "DASS-21", "4w", "0.015", 0.79,
             "but failed to reach significance until 4 weeks later ( p = 0.015, Hedges’ g = 0.79; p < 0.001, Hedges’ g = 0.69; p = 0.003, Hedges’ g = 0.66, respectively)",
             clin(**DASS, follow="4 weeks")),
        toad(E_4W, "DASS-21 anxiety, 4 weeks", "clinical", "decrease", "DASS-21", "4w", "<0.001", 0.69,
             "but failed to reach significance until 4 weeks later ( p = 0.015, Hedges’ g = 0.79; p < 0.001, Hedges’ g = 0.69; p = 0.003, Hedges’ g = 0.66, respectively)",
             clin(**DASS, follow="4 weeks")),
        toad(E_4W, "DASS-21 stress, 4 weeks", "clinical", "decrease", "DASS-21", "4w", "0.003", 0.66,
             "but failed to reach significance until 4 weeks later ( p = 0.015, Hedges’ g = 0.79; p < 0.001, Hedges’ g = 0.69; p = 0.003, Hedges’ g = 0.66, respectively)",
             clin(**DASS, follow="4 weeks")),
        toad(E_4W, "FFMQ-15 non-judgment (mindfulness), 4 weeks", "behavioral", "increase", "FFMQ-15", "4w",
             "0.009", 0.64, "Separate contrasts revealed improvements in non-judgment ( p = 0.009; Hedges’ g = 0.64)"),
        toad(E_4W, "BSI-18 depression, 4 weeks", "clinical", "decrease", "Brief Symptom Inventory 18", "4w",
             "0.023", 0.65,
             "but failed to reach significance until 4 weeks later ( p = 0.023, Hedges’ g = 0.65; p = 0.009, Hedges’ g = 0.81; p = 0.011, Hedges’ g = 0.85, respectively)",
             clin(scale="BSI-18", higher="worse", follow="4 weeks")),
        toad(E_4W, "Convergent thinking (Picture Concept Task correct solutions), 4 weeks", "behavioral",
             "increase", "Picture Concept Task", "4w", "0.002", 1.32,
             "and 4 weeks later ( p = 0.002; Hedges’ g = 1.32), as compared with baseline"),
    ])


import re as _re


def _clean(d):
    """Endpoint names carry no time point; time lives in time_value. Same outcome -> same key."""
    for v in d.values():
        for r in v["measurements"]:
            m = r["measurement"]
            name = m["endpoint_original"]
            name = _re.sub(r",\s*(full sample|day of post-treatment scan|(within )?\d[\d\-–]*\s*(h|weeks?|months?|days?)( post-treatment)?)$", "", name)
            name = _re.sub(r",\s*(full sample)$", "", name)
            m["endpoint_original"] = name
            if not m["endpoint_normalized"]:
                m["endpoint_normalized"] = _re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return d

_clean(drafts)
json.dump(drafts, open(OUT, "w"), indent=1, ensure_ascii=False)
print({k: len(v["measurements"]) for k, v in drafts.items()})

# --- PMC5021697: DMT protects human iPSC cortical neurons in hypoxia (added as dev) ---
E_IPSC = exp("Hypoxia (0.5% O2) assay, human iPSC-derived cortical neurons", "in_vitro", "human",
             "human iPSC-derived cerebral cortical neurons", 3, unit="other")
PC = dict(cell_type="iPSC-derived cerebral cortical neurons (Axol)", brain_region=None,
          culture_age_value=None, culture_age_unit=None, animal_age=None, sex=None,
          strain_or_line="Axol Bioscience iPSC-derived neural progenitors", probes=[])
SIG = dict(agent="Sig-1R siRNA", target="sigma-1 receptor", probe_type="genetic_knockdown",
           dose_value=None, dose_unit=None, effect_on_response="blocked")


def dmt_arm(dose, label=None, comp="Hypoxia control (no DMT)", comp_type="untreated"):
    return arm(label or f"DMT {dose:g} µM", "N,N-dimethyltryptamine", "DMT", dose, "µM",
               route="culture medium", regimen="added before hypoxia", comp_label=comp, comp_type=comp_type)


def ipsc(a, m, quote, probes=(), missing=()):
    r = row(E_IPSC, a, m, [anchor(quote)], None, missing)
    r["preclinical"] = {**PC, "probes": list(probes)}
    return r


SURV = "Neuronal survival under hypoxia (Annexin V flow cytometry)"
drafts2 = {"PMC5021697": dict(
    reports_measured_outcomes=True,
    screening_reason="In vitro study measuring survival and hypoxia markers in human iPSC neurons with DMT and a sigma-1 receptor knockdown.",
    measurements=[
        ipsc(dmt_arm(10), meas(SURV, "cellular", "increase", norm="neuron_survival_hypoxia",
             instrument="Annexin V-FITC flow cytometry", t=6, t_unit="hours", t_origin="hypoxia onset",
             value=31, unit="% surviving cells (median)", control=19, test=None, p="0.037"),
             "the administration of 10 and 50 μMs DMT elevated this value to a median of 31% (±6%, p = 0.037) and 64% (±5%, p = 0.006), respectively"),
        ipsc(dmt_arm(50), meas(SURV, "cellular", "increase", norm="neuron_survival_hypoxia",
             instrument="Annexin V-FITC flow cytometry", t=6, t_unit="hours", t_origin="hypoxia onset",
             value=64, unit="% surviving cells (median)", control=19, p="0.006"),
             "the administration of 10 and 50 μMs DMT elevated this value to a median of 31% (±6%, p = 0.037) and 64% (±5%, p = 0.006), respectively"),
        ipsc(dmt_arm(50, "DMT 50 µM + Sig-1R siRNA", comp="DMT 50 µM + control siRNA", comp_type="active"),
             meas(SURV, "cellular", "decrease", norm="neuron_survival_hypoxia",
                  instrument="Annexin V-FITC flow cytometry", t=6, t_unit="hours", t_origin="hypoxia onset",
                  p="<0.05"),
             "specific silencing of Sig-1R abrogated the modulatory potential of DMT on the survival (Figure 4B )",
             probes=[SIG], missing=[("measurement.value", "not_reported")]),
        ipsc(dmt_arm(50), meas("HIF-1α protein under hypoxia", "molecular", "decrease", norm="hif1a_protein",
             instrument="Western blot densitometry", t=6, t_unit="hours", t_origin="hypoxia onset", p="<0.05"),
             "the administration of 50 μM DMT prevented this increase in all cell types (Figures 3A,B )",
             missing=[("measurement.value", "not_reported")]),
        ipsc(dmt_arm(50), meas("VEGF mRNA under hypoxia", "molecular", "decrease", norm="vegf_mrna",
             instrument="qPCR", t=6, t_unit="hours", t_origin="hypoxia onset", p="<0.05"),
             "significantly decreased mRNA expressions of VEGF upon DMT treatment in all cell types under hypoxia",
             missing=[("measurement.value", "not_reported")]),
        ipsc(dmt_arm(50, "DMT 50 µM + Sig-1R siRNA", comp="DMT 50 µM + control siRNA", comp_type="active"),
             meas("HIF-1α protein under hypoxia", "molecular", "not_reported", norm="hif1a_protein",
                  instrument="Western blot densitometry", t=6, t_unit="hours", t_origin="hypoxia onset"),
             "Sig-1R gene silencing resulted in the ablation of the modulatory capacity of DMT on HIF-1α protein expression",
             probes=[SIG], missing=[("measurement.value", "not_reported")]),
    ])}
_clean(drafts2)
json.dump(drafts2, open(OUT.replace(".json", "_neuro.json"), "w"), indent=1, ensure_ascii=False)
print({k: len(v["measurements"]) for k, v in drafts2.items()})
