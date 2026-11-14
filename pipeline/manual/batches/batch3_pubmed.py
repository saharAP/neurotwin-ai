"""Batch 3: PubMed-search papers (neuron-level), hand-extracted in a Claude Code session (no API)."""
import sys

sys.path.insert(0, "..")
from helpers import anchor, arm, exp, meas, none, paper, pre, probe, prow, row, write  # noqa: E402

D = {}

# --- PMC13449763: DMT and proliferation of human iPSC-derived neural stem cells -------------------
NSC = pre(cell_type="iPSC-derived neural stem cells", strain="3 iPSC-derived NSC lines")


def nsc(dose, endpoint, norm, scale, direction, quote, instrument, value=None, unit=None, control=None, p=None,
        n=5, probes=(), comp=("vehicle", "vehicle"), es=None, es_type=None):
    e = exp("Human NSC culture", "in_vitro", "human", "human iPSC-derived neural stem cells", n, unit="other")
    lbl = f"DMT {dose:g} µM" + (" + " + ", ".join(p_["agent"] for p_ in probes) if probes else "")
    a = arm(lbl, "N,N-dimethyltryptamine", "DMT", dose, "µM", route="culture medium",
            comp_label=comp[0], comp_type=comp[1])
    miss = [] if value is not None else [("measurement.value", "not_reported")]
    return prow(e, a, meas(endpoint, scale, direction, norm=norm, instrument=instrument, t=24, t_unit="hours",
                           t_origin="DMT exposure", value=value, unit=unit, control=control, es_type=es_type,
                           es=es, p=p),
                [anchor(quote)], {**NSC, "probes": list(probes)}, miss)


D["PMC13449763"] = paper(
    "Human neural stem cell study measuring proliferation, cell-cycle markers and neurotrophin expression after DMT.",
    [
        nsc(1, "EdU+ proliferating cell fraction", "edu_proliferation", "neurogenesis", "increase",
            "reaching a maximum at 1 μM, corresponding to a 23.8% increase in proliferation over vehicle ( p = 0.0032, N = 5",
            "EdU incorporation", value=23.8, unit="% increase vs vehicle", es=23.8, es_type="percent_change", p="0.0032"),
        nsc(10, "EdU+ proliferating cell fraction", "edu_proliferation", "neurogenesis", "increase",
            "Significant elevations persisted at 10 μM ( p = 0.0089", "EdU incorporation", p="0.0089"),
        nsc(1, "EdU+ proliferating cell fraction", "edu_proliferation", "neurogenesis", "increase",
            "Co-treatment with the σ1R-antagonist BD-1063, instead, produced a small but significant increment in EdU + fraction compared to DMT alone ( p = 0.0456",
            "EdU incorporation", p="0.0456", comp=("DMT 1 µM alone", "active"),
            probes=[probe("BD-1063", "sigma-1 receptor", "antagonist", effect="enhanced")]),
        nsc(1, "Ki-67+ cycling cell fraction", "ki67_fraction", "neurogenesis", "increase",
            "DMT 1 μM increased the Ki-67 + fraction by 66.3% at 24 h, consistent with elevated cycling ( p = 0.0130, N = 5)",
            "Ki-67 immunostaining", value=66.3, unit="% increase vs vehicle", es=66.3, es_type="percent_change", p="0.0130"),
        nsc(1, "BDNF protein (intracellular)", "bdnf_protein", "molecular", "increase",
            "a marked 5.2-fold increase in total intracellular BDNF after DMT compared with vehicle (57.45 ± 11.62 pg/mg vs 10.95 ± 2.14 pg/mg; p = 0.0122, N = 3)",
            "ELISA", value=57.45, unit="pg/mg protein", control=10.95, p="0.0122", n=3),
        nsc(1, "BDNF mRNA", "bdnf_mrna", "molecular", "increase",
            "NGF and BDNF transcripts were upregulated by 9.5-fold (log 2 FC = 3.27 ± 0.14; p = 0.0018) and 4.6-fold (log 2 FC = 2.20 ± 0.39; p = 0.0228), respectively",
            "RT-qPCR", value=4.6, unit="fold vs vehicle", p="0.0228", n=4),
        nsc(1, "NGF mRNA", "ngf_mrna", "molecular", "increase",
            "NGF and BDNF transcripts were upregulated by 9.5-fold (log 2 FC = 3.27 ± 0.14; p = 0.0018)",
            "RT-qPCR", value=9.5, unit="fold vs vehicle", p="0.0018", n=4),
        nsc(1, "NTF3 mRNA", "ntf3_mrna", "molecular", "decrease",
            "NTF3 was markedly downregulated to 0.47-fold of vehicle (log 2 FC = – 1.08 ± 0.10; p = 0.0099, N = 4",
            "RT-qPCR", value=0.47, unit="fold vs vehicle", p="0.0099", n=4),
        nsc(1, "Neural stem cell viability", "nsc_viability", "cellular", "no_change",
            "DMT did not affect NSC viability across concentrations or exposure paradigms", "viability assay",
            p=">0.05", n=3),
    ])

# --- PMC12923610: single DMT dose in chronically stressed (UCMS) mice: behavior and neurogenesis ----
UCMS_PRE = lambda region=None, cell=None: pre(cell_type=cell, region=region, animal_age="postnatal day 45-70",  # noqa: E731
                                              sex="male", strain="DCXCreERT2::TdTOMlox/lox on C57BL/6")


def ucms(endpoint, norm, scale, direction, quote, instrument, p, comp=("UCMS + saline", "vehicle"), region=None,
         cell=None):
    e = exp("Chronic unpredictable mild stress model", "animal_in_vivo", "mouse",
            "male mice after 56 days of chronic mild stress", 8, unit="animal")
    a = arm("DMT 30 mg/kg i.p.", "N,N-dimethyltryptamine", "DMT", 30, "mg/kg", route="intraperitoneal",
            regimen="single dose after stress protocol", comp_label=comp[0], comp_type=comp[1])
    return prow(e, a, meas(endpoint, scale, direction, norm=norm, instrument=instrument, p=p,
                           test="one-way ANOVA with Tukey post-hoc"),
                [anchor(quote)], UCMS_PRE(region, cell),
                [("measurement.value", "not_reported"), ("measurement.time_value", "not_reported")])


DCX = "newborn granule cells (DCX-TOM+)"
D["PMC12923610"] = paper(
    "Mouse chronic-stress study of one DMT dose on anhedonia, despair, cognition and hippocampal neurogenesis.",
    [
        ucms("Sucrose preference (anhedonia)", "sucrose_preference", "behavioral", "increase",
             "All DMT-treated groups, including DMT alone, DMT under isoflurane, and DMT-d28, exhibited significantly higher sucrose preference compared to UCMS saline controls (all p < 0.0001)",
             "sucrose preference test", "<0.0001"),
        ucms("Immobility in tail suspension test", "tst_immobility", "behavioral", "decrease",
             "Remarkably, all tested treatments, i.e., DMT (p < 0.0001), DMT+Iso (p < 0.0001), fluoxetine (p = 0.0001), and DMT-d28 (p = 0.0002), effectively reduced immobility compared to UCMS saline controls",
             "tail suspension test", "<0.0001"),
        ucms("Pattern separation accuracy (hardest condition)", "pattern_separation", "behavioral", "increase",
             "animals treated with fluoxetine (p = 0.0007), DMT (p < 0.0001), and DMT+Iso (p = 0.0108) displayed significantly enhanced performance compared to the UCMS-saline group",
             "DNMP radial arm maze", "<0.0001"),
        ucms("Anxiety-like behavior (open field, elevated plus maze)", "anxiety_like_behavior", "behavioral",
             "no_change",
             "these results suggest that neither UCMS nor any of the pharmacological treatments tested induced measurable changes in anxiety-like behavior",
             "open field and elevated plus maze", None),
        ucms("New granule cells (DCX-TOM+), ventral dentate gyrus", "new_neurons_dg", "neurogenesis", "increase",
             "both the DMT and DMTd28 groups exhibited roughly a two-fold increase in DCX-TOM+ cell counts compared to non-stressed control animals (Non-UCMS vs. DMT p < 0.0001",
             "DCX-TOM cell counts", "<0.0001", comp=("non-stressed controls", "untreated"),
             region="ventral dentate gyrus", cell=DCX),
        ucms("New granule cells (DCX-TOM+), dorsal dentate gyrus", "new_neurons_dg", "neurogenesis", "increase",
             "all treatments led to markedly increased neurogenesis relative to UCMS-saline animals, including DMT (p < 0.0001)",
             "DCX-TOM cell counts", "<0.0001", region="dorsal dentate gyrus", cell=DCX),
    ])

if __name__ == "__main__":
    write(D, sys.argv[1])
