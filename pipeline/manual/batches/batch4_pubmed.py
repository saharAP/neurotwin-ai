"""Batch 4: remaining PubMed-search papers, hand-extracted in a Claude Code session (no API)."""
import sys

sys.path.insert(0, "..")
from helpers import clin, none, paper, q, write  # noqa: E402

D = {}

# --- PMC13198623: psilocybin dose-response in mice: receptor occupancy, behavior, synaptic markers --
MOUSE = dict(design="animal_in_vivo", species="mouse", pop="mice", drug="psilocybin",
             drug_norm="Psilocybin", dose_unit="mg/kg", route="subcutaneous", regimen="single dose")


def psi(dose, endpoint, scale, direction, quote, **kw):
    return q(kw.pop("exp_label", "Psilocybin dose-response"), MOUSE["design"], MOUSE["species"], MOUSE["pop"],
             kw.pop("n", None), endpoint, scale, direction, quote, drug=MOUSE["drug"],
             drug_norm=MOUSE["drug_norm"], dose=dose, dose_unit=MOUSE["dose_unit"], route=MOUSE["route"],
             regimen=MOUSE["regimen"], **kw)


D["PMC13198623"] = paper(
    "Mouse dose-response study of psilocybin on 5-HT2A occupancy, head-twitch, behavior and synaptic markers.",
    [
        psi(1, "Head-twitch response (total)", "behavioral", "increase",
            "the peak response ( E max = 31.66 HTRs; 95%CI: 28.47–34.97) was calculated to occur at a dose of 1 mg/kg",
            norm="head_twitch_total", instrument="head-twitch scoring", value=31.66, vunit="head twitches",
            unc="CI95", lo=28.47, hi=34.97),
        psi(10, "Locomotor activity", "behavioral", "decrease",
            "The higher doses of psilocybin (3.2–10 mg/kg, SC) also caused a significant decrease in the total locomotor activity over the duration of the session",
            norm="locomotor_activity", instrument="locomotor activity chamber"),
        psi(1.5, "Open arm time, elevated zero maze", "behavioral", "increase",
            "psilocybin-treated animals displayed a significantly increased open arms time ratio at the dose of 1.5 mg/kg, SC (22.83 ± 3.08%, n = 7, p < 0.05)",
            norm="ezm_open_arm_time", instrument="elevated zero maze", n=7, value=22.83, vunit="% open-arm time",
            control=13.82, unc="SEM", lo=3.08, p="<0.05", t=20, t_unit="hours", t_origin="administration"),
        psi(3, "Open arm time, elevated zero maze", "behavioral", "no_change",
            "but not at 3 mg/kg, SC (12.61 ± 2.31%, n = 6, p = 0.73), compared to vehicle-treated controls (13.82 ± 2.03%, n = 10)",
            norm="ezm_open_arm_time", instrument="elevated zero maze", n=6, value=12.61, vunit="% open-arm time",
            control=13.82, unc="SEM", lo=2.31, p="0.73", t=20, t_unit="hours", t_origin="administration"),
        psi(3, "Immobility, forced swim test", "behavioral", "decrease",
            "the immobility time was significantly reduced at 3 mg/kg, SC psilocybin (95.68 ± 9.60 seconds, n = 6, p < 0.001)",
            norm="fst_immobility", instrument="forced swim test", n=6, value=95.68, vunit="seconds",
            control=158.2, unc="SEM", lo=9.6, p="<0.001", t=24, t_unit="hours", t_origin="administration"),
        psi(1.5, "Immobility, forced swim test", "behavioral", "no_change",
            "but not at 1.5 mg/kg, SC psilocybin (171.0 ± 6.6 seconds, n = 8, p = 0.26), compared to vehicle controls (158.2 ± 8.23 seconds, n = 11)",
            norm="fst_immobility", instrument="forced swim test", n=8, value=171.0, vunit="seconds",
            control=158.2, unc="SEM", lo=6.6, p="0.26", t=24, t_unit="hours", t_origin="administration"),
        psi(1.5, "Acetylated alpha-tubulin", "molecular", "decrease",
            "1.5 mg/kg treatment elicited a 30.5% reduction in the PFC ( p = 0.0020 vs. Vehicle)",
            norm="acetylated_tubulin", instrument="Western blot", region="prefrontal cortex", value=-30.5,
            vunit="% change vs vehicle", es=-30.5, es_type="percent_change", p="0.0020"),
        psi(3, "Acetylated alpha-tubulin", "molecular", "decrease",
            "3 mg/kg treatment elicited a 45% reduction in the PFC ( p = 0.0001 vs. Vehicle) and 30% reduction in the amygdala ( p = 0.0001 vs. Vehicle)",
            norm="acetylated_tubulin", instrument="Western blot", region="prefrontal cortex", value=-45,
            vunit="% change vs vehicle", es=-45, es_type="percent_change", p="0.0001"),
        psi(1.5, "PSD-95 expression", "synaptic_structural", "increase",
            "PSD-95 expression was significantly increased in the PFC upon treatment with both 1.5 and 3 mg/kg (SC) psilocybin ( Figure 5(c) , Left), with a 32.4% and 33.3% increase, respectively",
            norm="psd95_expression", instrument="Western blot", region="prefrontal cortex", value=32.4,
            vunit="% change vs vehicle", es=32.4, es_type="percent_change", p="0.006"),
        psi(3, "PSD-95 expression", "synaptic_structural", "no_change",
            "In the amygdala, no significant changes were observed for PSD-95 expression upon treatment with 1.5 or 3 mg/kg psilocybin compared to vehicle-treated controls",
            norm="psd95_expression", instrument="Western blot", region="amygdala"),
        psi(3, "SV2A expression", "synaptic_structural", "increase",
            "with SV2A expression increased by 19.4% and 30.4%, respectively, compared to vehicle-treated controls (1.5 mg/kg; p = 0.0391, 3 mg/kg; p = 0.0046)",
            norm="sv2a_expression", instrument="Western blot", region="prefrontal cortex", value=30.4,
            vunit="% change vs vehicle", es=30.4, es_type="percent_change", p="0.0046"),
        psi(1.5, "Synaptophysin expression", "synaptic_structural", "increase",
            "Synaptophysin expression was significantly increased in the PFC after treatment with either 1.5 or 3 mg/kg (SC) psilocybin ( Figure 5(e) , Left), with 28.8% and 26.4% increases, respectively",
            norm="synaptophysin_expression", instrument="Western blot", region="prefrontal cortex", value=28.8,
            vunit="% change vs vehicle", es=28.8, es_type="percent_change", p="0.0077"),
    ])

# --- PMC12916285: halogenated DMT analogs: receptor binding, gene expression, dendrites, behavior ---
# The analogs (5-F/Cl/Br-DMT) are separate compounds, recorded under their own names.
def halo(drug, dose, endpoint, scale, direction, quote, **kw):
    return q(kw.pop("exp_label", "Halogenated DMT analog study"), kw.pop("design", "animal_in_vivo"),
             kw.pop("species", "mouse"), kw.pop("pop", "mice"), kw.pop("n", None), endpoint, scale, direction,
             quote, drug=drug, drug_norm=kw.pop("drug_norm", drug), dose=dose,
             dose_unit=kw.pop("dose_unit", "mg/kg"),
             route=kw.pop("route", "intraperitoneal"), regimen="single dose", **kw)


D["PMC12916285"] = paper(
    "Study of DMT and halogenated DMT analogs: receptor binding, plasticity gene expression, dendrite growth and behavior.",
    [
        halo("N,N-dimethyltryptamine", None, "5-HT2A receptor binding affinity (Ki)", "molecular", "not_reported",
             "K i \u00b1 SEM (nM) | 259 \u00b1 28 | 134 \u00b1 4 | 208 \u00b1 18 | 138 \u00b1 14",
             design="in_vitro", species="human (recombinant receptor)", pop="cells expressing human 5-HT2A receptor", unit="other",
             drug_norm="DMT", norm="5ht2a_binding_affinity", instrument="radioligand binding", value=259,
             vunit="nM (Ki)", unc="SEM", lo=28, comp="n/a (affinity measure)", comp_type="none",
             arm_label="DMT (binding assay)", location="table", section="Table 1"),
        halo("5-Br-DMT", None, "5-HT2A receptor binding affinity (Ki)", "molecular", "not_reported",
             "K i \u00b1 SEM (nM) | 259 \u00b1 28 | 134 \u00b1 4 | 208 \u00b1 18 | 138 \u00b1 14",
             design="in_vitro", species="human (recombinant receptor)", pop="cells expressing human 5-HT2A receptor", unit="other",
             norm="5ht2a_binding_affinity", instrument="radioligand binding", value=138, vunit="nM (Ki)",
             unc="SEM", lo=14, comp="n/a (affinity measure)", comp_type="none",
             arm_label="5-Br-DMT (binding assay)", location="table", section="Table 1"),
        halo("5-Br-DMT", 10, "Dendritic branches (Sholl analysis)", "cellular", "increase",
             "indicated a significant increment in number of crossings, number of primary dendrites, number of branches and total dendritic length",
             design="in_vitro", species="mouse", pop="mixed cortical neuron cultures", unit="cell",
             dose_unit="\u00b5M", route="culture medium", norm="dendritic_branches",
             instrument="MAP-2 immunocytochemistry, Sholl analysis", cell="cortical neurons (DIV4-7)",
             t=24, t_unit="hours", t_origin="start of exposure"),
        halo("5-Br-DMT", 10, "Total dendritic length", "cellular", "increase",
             "indicated a significant increment in number of crossings, number of primary dendrites, number of branches and total dendritic length",
             design="in_vitro", species="mouse", pop="mixed cortical neuron cultures", unit="cell",
             dose_unit="\u00b5M", route="culture medium", norm="dendritic_length",
             instrument="MAP-2 immunocytochemistry", cell="cortical neurons (DIV4-7)",
             t=24, t_unit="hours", t_origin="start of exposure"),
        halo("5-Br-DMT", 10, "Arc mRNA", "molecular", "increase",
             "revealed a significant increase in the expression of Arc for all DMT derivatives tested, in both the PFC and HIP",
             norm="arc_mrna", instrument="RT-qPCR", region="prefrontal cortex", t=30, t_unit="minutes",
             t_origin="administration"),
        halo("N,N-dimethyltryptamine", 10, "Arc mRNA", "molecular", "increase",
             "revealed a significant increase in the expression of Arc for all DMT derivatives tested, in both the PFC and HIP",
             drug_norm="DMT", norm="arc_mrna", instrument="RT-qPCR", region="hippocampus", t=30,
             t_unit="minutes", t_origin="administration"),
        halo("N,N-dimethyltryptamine", 10, "BDNF mRNA", "molecular", "no_change",
             "no significant differences were observed when analyzing Bdnf mRNA levels in PFC, HIP",
             drug_norm="DMT", norm="bdnf_mrna", instrument="RT-qPCR", region="prefrontal cortex", t=30,
             t_unit="minutes", t_origin="administration"),
        halo("5-Br-DMT", None, "Immobility, tail suspension test", "behavioral", "decrease",
             "on the test day, 5-Br-DMT-treated animals had a significantly lower immobilization time compared to saline-treated mice (Bonferroni\u2019s test, p < 0.05",
             norm="tst_immobility", instrument="tail suspension test", comp="saline", p="<0.05",
             t=24, t_unit="hours", t_origin="administration", arm_label="5-Br-DMT (TST dose)"),
        halo("N,N-dimethyltryptamine", None, "Head-twitch response", "behavioral", "increase",
             "ED 50 (mg/kg) (95% CI) | 1.10 (\u22120.15\u22122.35) | 0.887 (0.531\u22121.243) | 6.01 (3.85\u22128.17) | 21.6 (\u22124.5\u221247.6)",
             drug_norm="DMT", norm="head_twitch_total", instrument="head-twitch scoring", value=9.79,
             vunit="head twitches (Emax)", unc="CI95", lo=7.89, hi=11.68, arm_label="DMT (dose-response)",
             location="table", section="Table 1"),
        halo("5-Br-DMT", None, "Head-twitch response", "behavioral", "no_change",
             "with 5-Br-DMT failing to elicit a significant HTR compared to saline administration",
             norm="head_twitch_total", instrument="head-twitch scoring", comp="saline",
             arm_label="5-Br-DMT (dose-response)"),
    ])

# --- PMC13181311: DMT on mouse VTA neurons (brain slice electrophysiology) -------------------------
def vta(dose, sex, endpoint, direction, quote, n, **kw):
    return q("VTA brain slice patch clamp", "ex_vivo", "mouse", "VTA Ih-negative neurons in brain slices", n,
             endpoint, "synaptic_functional", direction, quote, unit="cell", drug="N,N-dimethyltryptamine",
             drug_norm="DMT", dose=dose, dose_unit=kw.pop("dose_unit", "nM"), route="bath application",
             comp="baseline (same cell)", comp_type="baseline_within_subject", cell="VTA neurons",
             region="ventral tegmental area", sex=sex, strain="NMRI mice", **kw)


D["PMC13181311"] = paper(
    "Brain-slice electrophysiology measuring DMT effects on membrane current in mouse VTA neurons.",
    [
        vta(500, "female", "Membrane holding current", "no_change",
            "there was no statistical difference between the average baseline holding current and the holding current recorded during application of 500 nM DMT (Baseline: \u221219.70 \u00b1 6.99 pA; 500 nM: \u221225.30 \u00b1 8.83 pA; n = 7",
            7, norm="membrane_holding_current", instrument="voltage-clamp recording", value=-25.30, vunit="pA",
            control=-19.70, unc="SEM", lo=8.83, test="Wilcoxon test", p="0.1562"),
        vta(90, "female", "Membrane holding current", "no_change",
            "or during application of 90 \u03bcM DMT (Baseline: \u221226.99 \u00b1 5.51 pA; 90 \u03bcM: \u221229.61 \u00b1 6.47 pA; n = 14",
            14, dose_unit="\u00b5M", norm="membrane_holding_current", instrument="voltage-clamp recording",
            value=-29.61, vunit="pA", control=-26.99, unc="SEM", lo=6.47, test="paired t-test", p="0.2181"),
        vta(500, "male", "Membrane holding current", "no_change",
            "the average membrane holding current did not significantly change in male VTA neurons when exposed to the lower DMT concentration (Baseline: \u221215.81 \u00b1 4.70 pA; 500 nM: \u221217.76 \u00b1 5.72 pA; n = 10",
            10, norm="membrane_holding_current", instrument="voltage-clamp recording", value=-17.76, vunit="pA",
            control=-15.81, unc="SEM", lo=5.72, test="paired t-test", p="0.3713"),
        vta(90, "male", "Membrane holding current", "no_change",
            "or to the higher DMT concentration (Baseline: \u221225.64 \u00b1 6.68 pA; 90 \u03bcM: \u221227.88 \u00b1 8.84 pA; n = 10",
            10, dose_unit="\u00b5M", norm="membrane_holding_current", instrument="voltage-clamp recording",
            value=-27.88, vunit="pA", control=-25.64, unc="SEM", lo=8.84, test="Wilcoxon test", p="0.4258"),
    ])

# --- PMC11291293: psilocybin desynchronizes human brain networks (precision fMRI) ------------------
def fc(endpoint, direction, quote, **kw):
    return q("Longitudinal precision functional mapping", "randomized_controlled_trial", "human",
             "healthy adults, ~18 MRI visits each", 6, endpoint, "circuit", direction, quote, unit="participant",
             drug="psilocybin", drug_norm="Psilocybin", dose=25, dose_unit="mg", route="oral",
             regimen="single high dose", comp="methylphenidate 40 mg", comp_type="active",
             instrument="resting-state fMRI functional connectivity", **kw)


D["PMC11291293"] = paper(
    "Precision fMRI study of acute and persistent psilocybin effects on human brain network connectivity.",
    [
        fc("Whole-brain functional connectivity change", "increase",
           "Psilocybin massively disrupted functional connectivity (FC) in cortex and subcortex, acutely causing more than threefold greater change than methylphenidate",
           norm="fc_change", es=3, es_type="ratio", section="Abstract"),
        fc("Functional connectivity change, association cortex", "increase",
           "FC change mean (standard deviation, s.d.): association cortex 0.44 (0.03), primary cortex 0.36 (0.05)",
           norm="fc_change_association_cortex", value=0.44, vunit="Euclidean distance from baseline",
           unc="SD", lo=0.03, region="association cortex"),
        fc("Functional connectivity change, primary cortex", "increase",
           "FC change mean (standard deviation, s.d.): association cortex 0.44 (0.03), primary cortex 0.36 (0.05)",
           norm="fc_change_primary_cortex", value=0.36, vunit="Euclidean distance from baseline",
           unc="SD", lo=0.05, region="primary cortex"),
        fc("Anterior hippocampus to default mode network connectivity", "decrease",
           "Psilocybin caused persistent decrease in FC between the anterior hippocampus and default mode network, lasting for weeks",
           norm="hippocampus_dmn_fc", region="anterior hippocampus", section="Abstract",
           t=3, t_unit="weeks", t_origin="dose"),
    ])

# --- PMC12364870: psilocybin retreat in veterans with TBI (observational, EEG + questionnaires) -----
def vet(endpoint, norm, scale, direction, quote, n, value=None, vunit=None, p_=None, clinical=None, **kw):
    return q("Psilocybin retreat, veterans with TBI", "observational", "human",
             "male veterans reporting traumatic brain injury", n, endpoint, scale, direction, quote,
             unit="participant", drug="psilocybin-containing mushrooms", drug_norm="Psilocybin",
             route="oral", regimen="retreat", comp="baseline (4 weeks pre-retreat)",
             comp_type="baseline_within_subject", arm_label="Psilocybin retreat (dose not reported)",
             norm=norm, value=value, vunit=vunit, p=p_, t=4, t_unit="weeks", t_origin="retreat",
             clinical=clinical, section="Abstract", **kw)


D["PMC12364870"] = paper(
    "Observational study of psilocybin retreat outcomes and EEG changes in veterans reporting traumatic brain injury.",
    [
        vet("PCL-5 PTSD score", "pcl5_score", "clinical", "decrease",
            "PTSD (PCL-5 scores decreased by 50%, p=0.010)", 13, -50, "% change", "0.010",
            clin(scale="PCL-5", higher="worse", follow="4 weeks"), instrument="PCL-5", es=-50,
            es_type="percent_change", test="paired t-test"),
        vet("PHQ-9 depression score", "phq9_score", "clinical", "decrease",
            "depression (PHQ-9 scores decreased by 65%, p<0.001)", 13, -65, "% change", "<0.001",
            clin(scale="PHQ-9", higher="worse", follow="4 weeks"), instrument="PHQ-9", es=-65,
            es_type="percent_change", test="paired t-test"),
        vet("STAI anxiety score", "stai_score", "clinical", "decrease",
            "anxiety (STAI) scores decreased by 28%, p<0.001)", 13, -28, "% change", "<0.001",
            clin(scale="STAI", higher="worse", follow="4 weeks"), instrument="STAI", es=-28,
            es_type="percent_change", test="paired t-test"),
        vet("EEG delta and theta power, frontal and temporal regions", "eeg_delta_theta_power", "circuit",
            "decrease",
            "EEG data showed decreased delta and theta power in frontal and temporal regions, indicating potential improvements in cognitive control and emotional processing",
            21, instrument="EEG frequency band analysis", region="frontal and temporal cortex"),
        vet("EEG alpha and beta coherence", "eeg_alpha_beta_coherence", "circuit", "increase",
            "Enhanced coherence in alpha and beta bands suggested improved neural communication", 21,
            instrument="EEG coherence analysis"),
    ])

# --- PMC12070030: 6-hour IV DMT infusion, safety and pharmacodynamics (phase 1) ---------------------
D["PMC12070030"] = paper(
    "Phase 1 randomized placebo-controlled study of a 6-hour intravenous DMT infusion in healthy participants.",
    [
        q("Randomized placebo-controlled dose escalation", "randomized_controlled_trial", "human",
          "healthy adults aged 19-57", 29, "Adverse events", "clinical", "increase",
          "All AEs were self\u2010limiting and mild to moderate in intensity. The most commonly occurring AEs were headache, nausea, and fatigue for DMT and fatigue for placebo",
          unit="participant", drug="N,N-dimethyltryptamine", drug_norm="DMT", route="intravenous",
          regimen="bolus plus 6-hour infusion, three dose levels", comp="placebo", comp_type="placebo",
          arm_label="DMT infusion (dose levels 1-3)", norm="adverse_events",
          instrument="adverse event reporting", section="Safety",
          clinical=clin(follow="study period")),
    ])

# --- PMC10206108: acute effects of IV DMT, randomized placebo-controlled --------------------------
def dmt_h(endpoint, norm, direction, quote, dose, dose_unit, arm_label, **kw):
    return q("Randomized placebo-controlled crossover", "randomized_controlled_trial", "human",
             "healthy participants", None, endpoint, "behavioral", direction, quote, unit="participant",
             drug="N,N-dimethyltryptamine", drug_norm="DMT", dose=dose, dose_unit=dose_unit,
             route="intravenous", comp=kw.pop("comp", "placebo"), comp_type=kw.pop("comp_type", "placebo"),
             arm_label=arm_label, norm=norm, **kw)


D["PMC10206108"] = paper(
    "Randomized placebo-controlled study of acute subjective effects of intravenous DMT bolus and infusion.",
    [
        dmt_h("Any drug effect rating", "subjective_any_drug_effect", "increase",
              "The higher infusion rate induced greater \u201cany drug effects\u201d ( p < 0.001) and \u201cgood drug effects\u201d ( p < 0.01) compared with the low infusion rate",
              1, "mg/min", "DMT high infusion (1 mg/min)", comp="low infusion (0.6 mg/min)",
              comp_type="active", instrument="visual analogue scale", p="<0.001"),
        dmt_h("Negative drug effects and anxiety", "subjective_negative_effects", "no_change",
              "The infusion of DMT did not produce negative drug effects or anxiety compared with placebo",
              0.6, "mg/min", "DMT low infusion (0.6 mg/min)", instrument="visual analogue scale"),
        dmt_h("Anxious ego dissolution (5D-ASC)", "anxious_ego_dissolution", "increase",
              "The high bolus dose led to more negative peak effects compared with the other conditions, reflected by significantly higher ratings of \u201cAnxious Ego Dissolution\u201d on the 5D-ASC",
              25, "mg", "DMT high bolus (25 mg) + high infusion", comp="other DMT conditions",
              comp_type="active", instrument="5D-ASC"),
    ])

if __name__ == "__main__":
    write(D, sys.argv[1])
