"""Helpers for hand-authored extraction drafts (no API): build Extraction-shaped dicts.

Each batch file in manual/batches/ builds {PMCID: {...}} with these helpers and writes JSON
that `extract.py --from-drafts` loads through the same quote check and schema validation.
"""
import json
import re


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




def pre(cell_type=None, region=None, age_value=None, age_unit=None, animal_age=None, sex=None,
        strain=None, probes=()):
    return dict(cell_type=cell_type, brain_region=region, culture_age_value=age_value,
                culture_age_unit=age_unit, animal_age=animal_age, sex=sex, strain_or_line=strain,
                probes=list(probes))


def probe(agent, target=None, kind="antagonist", dose=None, unit=None, effect=None):
    return dict(agent=agent, target=target, probe_type=kind, dose_value=dose, dose_unit=unit,
                effect_on_response=effect)


def prow(e, a, m, anchors, preclinical, missing=()):
    r = row(e, a, m, anchors, None, missing)
    r["preclinical"] = preclinical
    return r


def paper(reason, measurements, reports=True):
    return dict(reports_measured_outcomes=reports, screening_reason=reason, measurements=measurements)


def none(reason):
    return paper(reason, [], reports=False)


def clean(d):
    """Endpoint names carry no time point; same outcome -> same snake_case key."""
    for v in d.values():
        for r in v["measurements"]:
            m = r["measurement"]
            if not m["endpoint_normalized"]:
                m["endpoint_normalized"] = re.sub(r"[^a-z0-9]+", "_", m["endpoint_original"].lower()).strip("_")
    return d


def write(d, path):
    clean(d)
    json.dump(d, open(path, "w"), indent=1, ensure_ascii=False)
    print({k: len(v["measurements"]) for k, v in d.items()})


HUMAN_DESIGNS = {"randomized_controlled_trial", "nonrandomized_trial", "open_label_trial", "observational",
                 "case_report_or_series", "survey"}


def q(exp_label, design, species, pop, n, endpoint, scale, direction, quote, *, unit="animal",
      drug="", drug_norm="", dose=None, dose_unit=None, route=None, regimen=None, comp="vehicle",
      comp_type="vehicle", arm_label=None, norm=None, instrument=None, t=None, t_unit=None, t_origin=None,
      value=None, vunit=None, control=None, es=None, es_type=None, unc="none_reported", lo=None, hi=None,
      test=None, p=None, cell=None, region=None, sex=None, age=None, strain=None, probes=(), clinical=None,
      section="Results", location="text"):
    """One measurement in one call. Missing tracked fields get 'not_reported' when loaded."""
    e = exp(exp_label, design, species, pop, n, unit=unit)
    if arm_label is None:
        arm_label = f"{drug} {dose:g} {dose_unit}" if dose is not None else (drug or "intervention")
        if probes:
            arm_label += " + " + ", ".join(x["agent"] for x in probes)
    a = arm(arm_label, drug, drug_norm or drug, dose, dose_unit, route=route, regimen=regimen,
            comp_label=comp, comp_type=comp_type)
    m = meas(endpoint, scale, direction, norm=norm, instrument=instrument, t=t, t_unit=t_unit, t_origin=t_origin,
             value=value, unit=vunit, control=control, es_type=es_type, es=es, unc=unc, lo=lo, hi=hi,
             test=test, p=p)
    r = row(e, a, m, [anchor(quote, section=section, location=location)], clinical)
    if design not in HUMAN_DESIGNS:
        r["preclinical"] = pre(cell_type=cell, region=region, animal_age=age, sex=sex, strain=strain,
                               probes=list(probes))
    return r
