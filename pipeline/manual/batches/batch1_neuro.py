"""Batch 1: neuron-level papers, hand-extracted in a Claude Code session (no API).

Run from pipeline/manual/batches:  ../../../.venv/bin/python batch1_neuro.py ../../../data/evidence/manual_batch1.json
then from pipeline/:               ../.venv/bin/python extract.py --from-drafts ../data/evidence/manual_batch1.json
"""
import sys

sys.path.insert(0, "..")
from helpers import anchor, arm, exp, meas, none, paper, pre, probe, prow, row, write  # noqa: E402

D = {}

# --- PMC7830000: single psilocybin dose, pig brain SV2A (synaptic density) and 5-HT2A ---------
PIG_PRE = lambda region: pre(region=region, animal_age="approximately nine weeks", sex="female",  # noqa: E731
                             strain="Danish slaughter pigs (Yorkshire x Duroc x Landrace)")
E_PIG = exp("Awake pigs, single IV dose, post-mortem autoradiography", "animal_in_vivo", "pig",
            "female pigs, ~9 weeks old", 6, unit="animal")
A_PIG = arm("Psilocybin 0.08 mg/kg IV", "psilocybin", "Psilocybin", 0.08, "mg/kg", route="intravenous",
            regimen="single dose", comp_label="saline", comp_type="vehicle")


def pig(endpoint, norm, scale, region, day, value, direction, p, quote, instrument):
    return prow(E_PIG, A_PIG,
                meas(endpoint, scale, direction, norm=norm, instrument=instrument, t=day, t_unit="days",
                     t_origin="injection", value=value, unit="% difference vs saline",
                     es_type="percent_change", es=value, test="group comparison, Holm-adjusted", p=p),
                [anchor(quote)], PIG_PRE(region))


SV2A, HT2A_ANT, HT2A_AG = "SV2A synaptic density", "5-HT2A receptor density (antagonist radioligand)", "5-HT2A receptor density (agonist radioligand)"
UCB, MDL, CIMBI = "[3H]UCB-J autoradiography", "[3H]MDL100907 autoradiography", "[3H]Cimbi-36 autoradiography"
D["PMC7830000"] = paper(
    "Animal study measuring synaptic density (SV2A) and 5-HT2A receptor density after one psilocybin dose.",
    [
        pig(SV2A, "sv2a_density", "synaptic_structural", "hippocampus", 1, 4.42, "increase", "<0.0001",
            "psilocybin treatment was associated with 4.42% higher SV2A in the hippocampus ( p < 0.0001) one day after psilocybin injection", UCB),
        pig(SV2A, "sv2a_density", "synaptic_structural", "hippocampus", 7, 9.24, "increase", "0.024",
            "9.24% higher SV2A in the hippocampus ( p = 0.024) seven days after psilocybin", UCB),
        pig(SV2A, "sv2a_density", "synaptic_structural", "prefrontal cortex", 1, 0.25, "no_change", "1",
            "One day after psilocybin, there was no difference in PFC SV2A ( Figure 2 b and Table 1 , 0.25%, p = 1)", UCB),
        pig(SV2A, "sv2a_density", "synaptic_structural", "prefrontal cortex", 7, 6.10, "increase", "<0.0001",
            "seven days after psilocybin administration there was 6.10% higher SV2A in the PFC ( p < 0.0001)", UCB),
        pig(HT2A_ANT, "5ht2a_density_antagonist", "molecular", "hippocampus", 1, -29.60, "decrease", "<0.0001",
            "hippocampal 5-HT 2A R density ( Figure 2 a and Table 1 ) was 29.60% lower ( p < 0.0001)", MDL),
        pig(HT2A_ANT, "5ht2a_density_antagonist", "molecular", "prefrontal cortex", 1, -15.21, "no_change", "0.162",
            "PFC 5-HT 2A R density was similar (−15.21%, p = 0.162", MDL),
        pig(HT2A_ANT, "5ht2a_density_antagonist", "molecular", "hippocampus", 7, -3.58, "no_change", "1",
            "[ 3 H]MDL100907 (psilocybin vs. saline) | −29.60% ( p < 0.0001) | −3.58% ( p = 1) | −15.21% ( p = 0.162) | +1.32% ( p = 1)", MDL),
        pig(HT2A_ANT, "5ht2a_density_antagonist", "molecular", "prefrontal cortex", 7, 1.32, "no_change", "1",
            "[ 3 H]MDL100907 (psilocybin vs. saline) | −29.60% ( p < 0.0001) | −3.58% ( p = 1) | −15.21% ( p = 0.162) | +1.32% ( p = 1)", MDL),
        pig(HT2A_AG, "5ht2a_density_agonist", "molecular", "hippocampus", 1, -43.39, "decrease", "0.013",
            "hippocampal 5-HT 2A R/5-HT 2C R density ( Figure 2 c and Table 1 ) was 43.39% lower ( p = 0.013)", CIMBI),
        pig(HT2A_AG, "5ht2a_density_agonist", "molecular", "prefrontal cortex", 1, -50.19, "decrease", "<0.0001",
            "PFC 5-HT 2A R density ( Figure 2 d and Table 1 ) was 50.19% lower ( p < 0.0001)", CIMBI),
        pig(HT2A_AG, "5ht2a_density_agonist", "molecular", "hippocampus", 7, 3.31, "no_change", "1",
            "[ 3 H]Cimbi-36 (psilocybin vs. saline) | −43.39% ( p = 0.013) | +3.31% ( p = 1) | −50.19% ( p < 0.0001) | +2.23% ( p = 1)", CIMBI),
        pig(HT2A_AG, "5ht2a_density_agonist", "molecular", "prefrontal cortex", 7, 2.23, "no_change", "1",
            "[ 3 H]Cimbi-36 (psilocybin vs. saline) | −43.39% ( p = 0.013) | +3.31% ( p = 1) | −50.19% ( p < 0.0001) | +2.23% ( p = 1)", CIMBI),
    ])

# --- PMC6131656: single ICV 5-MeO-DMT, adult mouse dentate gyrus neurogenesis -----------------
A_5MEO = arm("5-MeO-DMT 100 µg ICV", "5-MeO-DMT", "5-MeO-DMT", 100, "µg", route="intracerebroventricular",
             regimen="single injection", comp_label="10% DMSO in saline", comp_type="vehicle")
MOUSE = dict(animal_age="55-70 days", sex="both", strain="C57BL6J and DCX-CreERT2::tdTomlox/lox")


def mouse(label, n, unit, endpoint, norm, scale, cell, t, t_unit, t_origin, value, vunit, control, p, quote,
          instrument, missing=()):
    e = exp(label, "animal_in_vivo", "mouse", "adult mice", n, unit=unit)
    return prow(e, A_5MEO, meas(endpoint, scale, "increase", norm=norm, instrument=instrument, t=t, t_unit=t_unit,
                                t_origin=t_origin, value=value, unit=vunit, control=control,
                                test="unpaired t-test", p=p),
                [anchor(quote)], pre(cell_type=cell, region="ventral dentate gyrus", **MOUSE), missing)


GC = "newborn dentate gyrus granule cells (DCX::tdTom+)"
D["PMC6131656"] = paper(
    "Mouse study measuring hippocampal cell proliferation, new-neuron survival, dendritic growth and synaptic input after one 5-MeO-DMT dose.",
    [
        mouse("BrdU proliferation assay", 5, "animal", "BrdU+ proliferating cells in dentate gyrus", "brdu_cells_dg",
              "neurogenesis", "proliferating progenitor cells", 12, "hours", "BrdU injection", 352.6, "cells per animal",
              155.4, "0.0029",
              "5-MeO-DMT treated: 352.6 ± 41.48 BrdU+ cells per animal, n = 5 mice. p = 0.0029, unpaired t -test",
              "BrdU immunohistochemistry"),
        mouse("BrdU proliferation assay", 5, "animal", "BrdU+ cell clusters in dentate gyrus", "brdu_clusters_dg",
              "neurogenesis", "proliferating progenitor cells", 12, "hours", "BrdU injection", 11.7, "clusters per section",
              5.964, "0.0002",
              "5-MeO-DMT treated: 11.7 ± 0.6974 clusters per section, eight sections were analyzed per mice, n = 5 mice. p = 0.0002",
              "BrdU immunohistochemistry"),
        mouse("DCX-CreERT2 fate mapping", 6, "animal", "New granule cells surviving (DCX::tdTom+)", "new_neurons_dg",
              "neurogenesis", GC, 21, "days", "injection", 220.3, "cells", 104, "0.0006",
              "5-MeO-DMT treated 220.3 ± 22.86 DCX::tdTom+ cells, n = 6 mice, p = 0.0006",
              "DCX::tdTom cell counts"),
        mouse("Morphology of newborn granule cells", 15, "cell", "Dendritic branch number", "dendritic_branches",
              "cellular", GC, 21, "days", "injection", 12.6, "branches per cell", 7.15, "0.0001",
              "5-MeO-DMT treated: 12.6 ± 0.916 dendritic branches, n = 15 cells from six mice, p = 0.0001",
              "neuron tracing (ImageJ)"),
        mouse("Morphology of newborn granule cells", 15, "cell", "Sholl intersections at 100 µm from soma",
              "sholl_intersections_100um", "cellular", GC, 21, "days", "injection", 6.357, "intersections", 3.6, "0.0001",
              "100 μm, 6.357 ± 0.561", "Sholl analysis"),
        mouse("Patch clamp of newborn granule cells", None, "cell", "sEPSC frequency", "sepsc_frequency",
              "synaptic_functional", GC, 21, "days", "injection", 1.35, "Hz", 0.35, "0.002",
              "the frequency of sEPSC was drastically increased in tdTomato+ GC of 5-MeO-DMT-treated mice when compared to controls (1.35 ± 0.22 Hz vs. 0.35 ± 0.07 Hz, respectively, p = 0.002",
              "whole-cell patch clamp", missing=[("experiment.n", "ambiguous")]),
        mouse("Patch clamp of newborn granule cells", None, "cell", "sEPSC amplitude", "sepsc_amplitude",
              "synaptic_functional", GC, 21, "days", "injection", 57.15, "pA", 37.72, "0.03",
              "sEPSC amplitude was greater in tdTomato+ cells of 5-MeO-DMT-treated mice im comparison to controls (57.15 ± 4.68 pA vs. 37.72 ± 6.60 pA, respectively, p = 0.03",
              "whole-cell patch clamp", missing=[("experiment.n", "ambiguous")]),
    ])

# --- PMC6639775: chronic intermittent low-dose DMT ("microdosing") in rats -----------------------
A_MICRO = arm("DMT 1 mg/kg every third day", "N,N-dimethyltryptamine", "DMT", 1, "mg/kg", route="intraperitoneal",
              regimen="every third day for about 7 weeks", comp_label="vehicle", comp_type="vehicle")


def rat(label, n, unit, endpoint, norm, scale, direction, p, quote, instrument, sex="both", cell=None, region=None,
        t=None, missing=(), test=None):
    e = exp(label, "animal_in_vivo", "rat", "young adult rats (from postnatal day 56)", n, unit=unit)
    miss = [("measurement.value", "not_reported"), *missing]
    if t is None:
        miss.append(("measurement.time_value", "ambiguous"))
    return prow(e, A_MICRO, meas(endpoint, scale, direction, norm=norm, instrument=instrument,
                                 t=t, t_unit="weeks" if t else None, t_origin="first dose" if t else None,
                                 test=test, p=p),
                [anchor(quote)], pre(cell_type=cell, region=region, animal_age="postnatal day 56 at start", sex=sex),
                miss)


L5 = "layer V pyramidal neurons"
D["PMC6639775"] = paper(
    "Rat study of repeated low DMT doses measuring behavior, prefrontal spine density and gene expression.",
    [
        rat("Golgi-Cox spine analysis, females", 20, "cell", "Dendritic spine density", "spine_density",
            "synaptic_structural", "decrease", "0.03",
            "DMT-treated females showed a significant decrease in the number of spines per 10 μm as compared to vehicle controls ( p = 0.03)",
            "Golgi-Cox staining", sex="female", cell=L5, region="prefrontal cortex", t=7),
        rat("Golgi-Cox spine analysis, males", 12, "cell", "Dendritic spine density", "spine_density",
            "synaptic_structural", "no_change", "0.98",
            "We observed comparable spine density in the PFC of both the vehicle- and DMT-treated male animals ( p = 0.98)",
            "Golgi-Cox staining", sex="male", cell=L5, region="prefrontal cortex", t=7),
        rat("Fear conditioning and extinction", 11, "animal", "Freezing during cued extinction memory test",
            "cued_extinction_freezing", "behavioral", "decrease", "0.03",
            "the DMT-treated animals froze significantly less than the vehicle controls ( p = 0.03)",
            "fear conditioning / cued extinction"),
        rat("Forced swim test, females", None, "animal", "Immobility in forced swim test", "fst_immobility",
            "behavioral", "decrease", "0.02", "Treatment significantly decreased immobility for females ( p = 0.02)",
            "forced swim test", sex="female", missing=[("experiment.n", "not_reported")]),
        rat("Elevated plus maze", None, "animal", "EPM anxiety score", "epm_score", "behavioral", "no_change", "0.92",
            "Animals treated with DMT were indistinguishable from vehicle controls ( p = 0.92)", "elevated plus maze",
            missing=[("experiment.n", "not_reported")]),
        rat("Novelty-induced locomotion", None, "animal", "NIL anxiety score", "nil_score", "behavioral", "no_change",
            "0.08",
            "Chronic, intermittent, low doses of DMT did not produce a significant difference between treatment groups in the NIL Score ( p = 0.08)",
            "novelty-induced locomotion", missing=[("experiment.n", "not_reported")]),
        rat("Prefrontal gene expression", None, "animal", "BDNF expression", "bdnf_expression", "molecular",
            "no_change", None,
            "Furthermore, it did not increase the expression of BDNF, a result that contrasts with increased BDNF expression",
            "droplet digital PCR", region="prefrontal cortex", t=7, missing=[("experiment.n", "not_reported")]),
    ])

# --- PMC4655865: psilocin in rats, fMRI BOLD, blood flow and neuronal (LFP) responses -----------
def psi_rat(dose, label, endpoint, norm, direction, quote, instrument, region=None):
    e = exp(label, "animal_in_vivo", "rat", "adult rats", None, unit="animal")
    a = arm(f"Psilocin {dose:g} mg/kg", "psilocin", "Psilocin", dose, "mg/kg", regimen="single dose",
            comp_label="vehicle", comp_type="vehicle")
    return prow(e, a, meas(endpoint, "circuit", direction, norm=norm, instrument=instrument),
                [anchor(quote)], pre(region=region),
                [("experiment.n", "not_reported"), ("measurement.value", "not_reported"),
                 ("measurement.time_value", "not_reported")])


D["PMC4655865"] = paper(
    "Rat imaging and electrophysiology study of acute psilocin effects on BOLD signal, blood flow and neuronal responses.",
    [
        psi_rat(2, "BOLD fMRI", "BOLD signal", "bold_signal", "decrease",
                "decreases in BOLD signal in the cingulate cortex and somatosensory cortex after drug administration in animals receiving 2 mg/kg psilocin",
                "BOLD fMRI", region="cingulate and somatosensory cortex"),
        psi_rat(2, "BOLD fMRI", "BOLD signal", "bold_signal", "increase",
                "but an increased BOLD signal in the hypothalamus and amygdala", "BOLD fMRI",
                region="hypothalamus and amygdala"),
        psi_rat(0.03, "BOLD fMRI", "BOLD signal", "bold_signal", "decrease",
                "At a dose of 0.03 mg/kg psilocin produced a small BOLD signal decrease in the cerebellum compared to vehicle treated controls but had no effect in other regions",
                "BOLD fMRI", region="cerebellum"),
        psi_rat(2, "Whisker stimulation, haemodynamics", "Blood flow response to whisker stimulation",
                "cbf_stimulus_response", "increase",
                "Psilocin treated animals showed increased haemodynamic response amplitude to whisker stimulation following drug administration",
                "laser Doppler / haemodynamic recording", region="somatosensory (barrel) cortex"),
        psi_rat(2, "Whisker stimulation, electrophysiology", "Neuronal response to whisker stimulation (LFP)",
                "lfp_stimulus_response", "decrease",
                "psilocin treated animals showed a significant reduction in neuronal response magnitude",
                "local field potential recording", region="somatosensory (barrel) cortex"),
    ])

# --- PMC4032947: psilocin and spatial memory in rats ---------------------------------------------
def mem(dose, label, endpoint, norm, direction, quote, instrument, p=None):
    e = exp(label, "animal_in_vivo", "rat", "adult rats", None, unit="animal")
    a = arm(f"Psilocin {dose:g} mg/kg s.c.", "psilocin", "Psilocin", dose, "mg/kg", route="subcutaneous",
            comp_label="saline", comp_type="vehicle")
    return prow(e, a, meas(endpoint, "behavioral", direction, norm=norm, instrument=instrument, p=p),
                [anchor(quote)], pre(),
                [("experiment.n", "not_reported"), ("measurement.value", "not_reported"),
                 ("measurement.time_value", "not_applicable")])


D["PMC4032947"] = paper(
    "Rat study of psilocin effects on spatial memory acquisition, retrieval and consolidation.",
    [
        mem(1, "Carousel maze acquisition", "Entrances into shock sector (errors)", "carousel_errors", "increase",
            "The group treated with the low dose of psilocin (1 mg/kg) showed significant impairment in solving the Carousel maze task in sessions 3 and 4",
            "Carousel maze", "<0.05"),
        mem(4, "Carousel maze acquisition", "Entrances into shock sector (errors)", "carousel_errors", "increase",
            "The group treated with the higher dose of psilocin 4 mg/kg showed significant impairment in solving the Carousel maze in sessions 3 through 5",
            "Carousel maze", "<0.05"),
        mem(1, "Carousel maze acquisition", "Locomotor activity", "locomotion", "no_change",
            "There was no significant difference between the control group and the group treated with 1 mg/kg of psilocin ( P > 0.05) during all five sessions",
            "Carousel maze", ">0.05"),
        mem(4, "Carousel maze acquisition", "Locomotor activity", "locomotion", "decrease",
            "These results show that a dose of 4 mg/kg of psilocin induced a decrease in locomotor activity",
            "Carousel maze", "<0.05"),
        mem(4, "Morris water maze retrieval", "Memory retrieval (escape latency)", "mwm_retrieval_latency", "increase",
            "Post hoc tests indicated that the retrieval was impaired in the group treated with a 4-mg/kg dose ( P < 0.01)",
            "Morris water maze", "<0.01"),
        mem(4, "Morris water maze consolidation", "Memory consolidation", "mwm_consolidation", "no_change",
            "Psilocin did not affect the consolidation in the MWM", "Morris water maze", "0.3390"),
    ])

# --- PMC7952974: low-dose psilocybin in rats: locomotion, 5-HT2A behaviors, motivation, attention ----
def lowpsi(label, n, dose, endpoint, norm, direction, quote, instrument, value=None, unit=None, control=None,
           p=None, probes=(), comp=("vehicle", "vehicle"), missing=()):
    e = exp(label, "animal_in_vivo", "rat", "adult rats", n, unit="animal")
    lbl = f"Psilocybin {dose:g} mg/kg SC" if dose is not None else "Psilocybin 0.05-0.1 mg/kg SC"
    if probes:
        lbl += " + " + ", ".join(pr["agent"] for pr in probes)
    a = arm(lbl, "psilocybin", "Psilocybin", dose, "mg/kg" if dose is not None else None, route="subcutaneous",
            comp_label=comp[0], comp_type=comp[1])
    miss = list(missing)
    if value is None:
        miss.append(("measurement.value", "not_reported"))
    if n is None:
        miss.append(("experiment.n", "not_reported"))
    if dose is None:
        miss.append(("arm.dose_value", "ambiguous"))
    miss.append(("measurement.time_value", "not_reported"))
    return prow(e, a, meas(endpoint, "behavioral", direction, norm=norm, instrument=instrument, value=value,
                           unit=unit, control=control, p=p),
                [anchor(quote)], pre(probes=probes), miss)


D["PMC7952974"] = paper(
    "Rat study of low psilocybin doses on locomotion, 5-HT2A-mediated behaviors, food motivation and attention.",
    [
        lowpsi("Open field locomotion", None, 0.3, "Distance traveled", "distance_traveled", "increase",
               "psilo 0.3 mg/kg: 5,716 ± 399; p = 0.04", "open field", value=5716, unit="cm", control=4141, p="0.04"),
        lowpsi("5-HT2A antagonist pretreatment", None, 1, "Wet dog shakes / back muscle contractions",
               "wds_bmc", "decrease",
               "(Veh/Psilocybin: 35.9 ± 4.9; M100907/Psilocybin: 0.7 ± 0.3; p < 0.001)", "behavioral scoring",
               value=0.7, unit="incidence score", control=35.9, p="<0.001",
               probes=[{"agent": "M100907", "target": "5-HT2A receptor", "probe_type": "antagonist",
                        "dose_value": 0.5, "dose_unit": "mg/kg", "effect_on_response": "blocked"}],
               comp=("psilocybin 1 mg/kg alone", "active")),
        lowpsi("Progressive ratio, low performers", 24, None, "Lever presses for food (motivation)",
               "pr_lever_presses", "increase",
               "reflecting increases in both measures following psilocybin 0.05–0.1 mg/kg pretreatment relative to vehicle",
               "progressive ratio task", p="<0.01"),
        lowpsi("Progressive ratio, all rats", 72, None, "Lever presses for food (motivation)", "pr_lever_presses",
               "no_change",
               "there was no main effect of treatment on number of lever press (F3,210 = 1.9, p = 0.1; NS",
               "progressive ratio task", p="0.1"),
        lowpsi("5-choice serial reaction time task", 24, 0.1, "Attention accuracy (% correct)", "fivecsrtt_pct_correct",
               "no_change", "Psilocybin (0.1 mg/kg) | 70.0 ± 3.2 | 9.8 ± 1.2 | 15.8 ± 2.8 | 87.7 ± 1.5",
               "5-CSRTT", value=87.7, unit="% correct", control=85.2),
    ])

# --- PMC7577737: IV DMT and cortical travelling waves (EEG), healthy volunteers --------------------
E_DMTEEG = exp("Placebo-controlled within-subject EEG study", "nonrandomized_trial", "human",
               "healthy volunteers, eyes closed", 13)
A_DMTIV = arm("DMT IV (7-20 mg)", "N,N-dimethyltryptamine", "DMT", None, None, route="intravenous",
              regimen="single injection; 7, 14, 18 or 20 mg by participant", comp_label="placebo",
              comp_type="placebo")
EEG_MISS = [("arm.dose_value", "ambiguous"), ("measurement.value", "not_reported"),
            ("measurement.time_value", "ambiguous")]


def wave(endpoint, norm, direction, quote):
    return row(E_DMTEEG, A_DMTIV, meas(endpoint, "circuit", direction, norm=norm, instrument="EEG, 2D-FFT wave analysis"),
               [anchor(quote)], None, EEG_MISS)


D["PMC7577737"] = paper(
    "Human EEG study of travelling cortical waves after intravenous DMT versus placebo.",
    [
        wave("Forward (posterior-to-anterior) travelling waves", "eeg_forward_waves", "increase",
             "whereas the amount of FW waves increased significantly above zero (BF 10 = 5.4 95% CI: [0.027, 0.336])"),
        wave("Backward (anterior-to-posterior) travelling waves", "eeg_backward_waves", "decrease",
             "the amount of BW waves decreased (but remaining significantly above zero – BFs 10 = 12.6, 95% CI: [0.057, 0.322])"),
        wave("Left-right travelling waves", "eeg_lateral_waves", "no_change",
             "waves propagating from leftward to rightward regions (and vice versa), were not affected by DMT"),
    ])

# --- PMC4732191: psilocybin and threat-induced amygdala connectivity (fMRI DCM) ---------------------
E_AMG = exp("Randomized double-blind placebo-controlled crossover fMRI", "randomized_controlled_trial", "human",
            "healthy adults", 23)
A_AMG = arm("Psilocybin 0.16 mg/kg oral", "psilocybin", "Psilocybin", 0.16, "mg/kg", route="oral",
            regimen="single dose", comp_label="placebo", comp_type="placebo")
D["PMC4732191"] = paper(
    "Randomized crossover fMRI study of psilocybin effects on threat-related amygdala-visual cortex connectivity.",
    [
        row(E_AMG, A_AMG, meas("Threat-induced modulation of amygdala to visual cortex connectivity", "circuit",
                               "decrease", norm="amygdala_v1_threat_modulation", instrument="fMRI dynamic causal modeling",
                               value=0.030, unit="Hz", control=0.526, unc="SD", lo=0.14,
                               test="Duncan's multiple range test", p="0.01"),
            [anchor("the threat-induced modulation of AMY → V1 connectivity was significantly reduced after psilocybin compared to placebo administration (p = 0.01; Duncan's multiple range test corrected)")],
            None, [("measurement.time_value", "not_reported")]),
        row(E_AMG, A_AMG, meas("Endogenous amygdala-visual-prefrontal connectivity", "circuit", "no_change",
                               norm="endogenous_amg_connectivity", instrument="fMRI dynamic causal modeling", p=">0.05"),
            [anchor("There was no significant effect of psilocybin on endogenous or input parameters (all p > 0.05)")],
            None, [("measurement.value", "not_reported"), ("measurement.time_value", "not_reported")]),
    ])

if __name__ == "__main__":
    write(D, sys.argv[1])
