"""Batch 5: clinical psilocybin papers, hand-extracted in a Claude Code session (no API)."""
import sys

sys.path.insert(0, "..")
from helpers import clin, none, paper, q, write  # noqa: E402

D = {}

# --- PMC7643046: psilocybin-assisted therapy for major depression (randomized waitlist) ------------
def mdd(endpoint, norm, direction, quote, **kw):
    return q("Randomized waiting-list controlled trial", "randomized_controlled_trial", "human",
             "adults with major depressive disorder", 24, endpoint, "clinical", direction, quote,
             unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=25, dose_unit="mg/70 kg",
             route="oral", regimen="two sessions with psychological support",
             comp="delayed treatment (waiting list)", comp_type="waitlist",
             arm_label="Immediate psilocybin treatment", norm=norm, **kw)


D["PMC7643046"] = paper(
    "Randomized trial of psilocybin-assisted therapy for major depressive disorder, with GRID-HAMD outcomes.",
    [
        mdd("GRID-HAMD depression score", "gridhamd_score", "decrease",
            "In the immediate treatment group, the mean (SD) GRID-HAMD scores were 22.9 (3.6) at baseline, 8.0 (7.1) at week 5, and 8.5 (5.7) at week 8",
            instrument="GRID-HAMD", value=8.0, vunit="points", control=23.8, unc="SD", lo=7.1,
            t=5, t_unit="weeks", t_origin="baseline", test="independent samples t-test",
            clinical=clin(scale="GRID-HAMD", higher="worse", blind="no", follow="week 5")),
        mdd("GRID-HAMD depression score", "gridhamd_score", "decrease",
            "In the immediate treatment group, the mean (SD) GRID-HAMD scores were 22.9 (3.6) at baseline, 8.0 (7.1) at week 5, and 8.5 (5.7) at week 8",
            instrument="GRID-HAMD", value=8.5, vunit="points", control=23.5, unc="SD", lo=5.7,
            t=8, t_unit="weeks", t_origin="baseline", test="independent samples t-test",
            clinical=clin(scale="GRID-HAMD", higher="worse", blind="no", follow="week 8")),
        mdd("Time by condition interaction on depression", "gridhamd_interaction", "decrease",
            "A statistically significant time by condition interaction effect on GRID-HAMD was found (η p 2 = 0.57; 90% CI, 0.38-0.66; P < .001)",
            instrument="GRID-HAMD", value=0.57, vunit="partial eta squared", unc="CI_other", lo=0.38, hi=0.66,
            p="<0.001", t=8, t_unit="weeks", t_origin="baseline",
            clinical=clin(scale="GRID-HAMD", higher="worse", blind="no")),
    ])

# --- PMC5367557: psilocybin for depression and anxiety in cancer patients (crossover RCT) ----------
def cancer(endpoint, norm, scale, direction, quote, **kw):
    return q("Randomized double-blind crossover trial", "randomized_controlled_trial", "human",
             "cancer patients with depression and/or anxiety", 51, endpoint, scale, direction, quote,
             unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=22, dose_unit="mg/70 kg",
             route="oral", regimen="high dose, crossover with low dose 5 weeks apart",
             comp="low (placebo-like) dose 1-3 mg/70 kg", comp_type="active",
             arm_label="Psilocybin high dose (22-30 mg/70 kg)", norm=norm, **kw)


D["PMC5367557"] = paper(
    "Crossover trial of high- versus low-dose psilocybin for depression and anxiety in cancer patients.",
    [
        cancer("Clinician- and self-rated depressed mood and anxiety", "depression_anxiety_ratings", "clinical",
               "decrease",
               "High-dose psilocybin produced large decreases in clinician- and self-rated measures of depressed mood and anxiety, along with increases in quality of life, life meaning, and optimism, and decreases in death anxiety",
               instrument="GRID-HAMD, HAM-A and self-report scales", section="Abstract",
               clinical=clin(scale="GRID-HAMD / HAM-A", higher="worse", blind="yes")),
        cancer("Clinically significant decrease in depressed mood and anxiety at 6 months",
               "depression_anxiety_response", "clinical", "decrease",
               "At 6-month follow-up, these changes were sustained, with about 80% of participants continuing to show clinically significant decreases in depressed mood and anxiety",
               instrument="GRID-HAMD, HAM-A", value=80, vunit="% of participants", t=6, t_unit="months",
               t_origin="session", section="Abstract",
               clinical=clin(scale="GRID-HAMD / HAM-A", higher="worse", resp=0.80,
                             resp_def="clinically significant decrease in depressed mood and anxiety",
                             follow="6 months")),
        cancer("Elevated systolic blood pressure during session", "elevated_systolic_bp", "clinical", "increase",
               "an episode of elevated systolic blood pressure (>160 mm Hg at one or more time-point) occurred in 34% of participants in the high-dose session and 17% of participants in the low-dose session",
               instrument="blood pressure monitoring", value=34, vunit="% of participants", control=17,
               section="Adverse effects", clinical=clin(blind="yes")),
        cancer("Nausea or vomiting during session", "nausea_vomiting", "clinical", "increase",
               "Nausea or vomiting occurred in 15% of participants in the high-dose session and none in the low-dose session",
               instrument="adverse event reporting", value=15, vunit="% of participants", control=0,
               section="Adverse effects", clinical=clin(blind="yes")),
        cancer("Anxiety episode during session", "session_anxiety", "clinical", "increase",
               "An episode of anxiety occurred in 26% of participants in the high-dose session and 15% in the low-dose session",
               instrument="monitor ratings", value=26, vunit="% of participants", control=15,
               section="Adverse effects", clinical=clin(blind="yes")),
    ])

# --- PMC5813086: open-label psilocybin for treatment-resistant depression, 6 months ----------------
def trd(endpoint, norm, direction, quote, **kw):
    return q("Open-label trial", "open_label_trial", "human",
             "adults with treatment-resistant major depression", 20, endpoint, "clinical", direction, quote,
             unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=25, dose_unit="mg",
             route="oral", regimen="10 mg then 25 mg, 7 days apart", comp="baseline",
             comp_type="baseline_within_subject", arm_label="Psilocybin (10 mg then 25 mg)",
             norm=norm, instrument="QIDS-SR16", section="Abstract", **kw)


D["PMC5813086"] = paper(
    "Open-label trial of two psilocybin doses for treatment-resistant depression, followed to 6 months.",
    [
        trd("QIDS-SR16 depression score", "qids_sr16_depression_score", "decrease",
            "marked reductions in depressive symptoms were observed for the first 5 weeks post-treatment (Cohen\u2019s d = 2.2 at week 1 and 2.3 at week 5, both p < 0.001)",
            es=2.2, es_type="standardized_mean_difference", p="<0.001", t=1, t_unit="weeks",
            t_origin="treatment", clinical=clin(scale="QIDS-SR16", higher="worse", blind="no", follow="1 week")),
        trd("QIDS-SR16 depression score", "qids_sr16_depression_score", "decrease",
            "marked reductions in depressive symptoms were observed for the first 5 weeks post-treatment (Cohen\u2019s d = 2.2 at week 1 and 2.3 at week 5, both p < 0.001); nine and four patients met the criteria for response and remission at week 5",
            es=2.3, es_type="standardized_mean_difference", p="<0.001", t=5, t_unit="weeks",
            t_origin="treatment",
            clinical=clin(scale="QIDS-SR16", higher="worse", blind="no", resp=0.45, remis=0.20,
                          resp_def="response criteria at week 5 (9 of 20 patients)", follow="5 weeks")),
        trd("QIDS-SR16 depression score", "qids_sr16_depression_score", "decrease",
            "Results remained positive at 3 and 6 months (Cohen\u2019s d = 1.5 and 1.4, respectively, both p < 0.001)",
            es=1.4, es_type="standardized_mean_difference", p="<0.001", t=6, t_unit="months",
            t_origin="treatment", clinical=clin(scale="QIDS-SR16", higher="worse", blind="no", follow="6 months")),
    ])

# --- PMC8864328: psilocybin for MDD, 12-month follow-up -------------------------------------------
def mdd12(endpoint, norm, direction, quote, **kw):
    return q("Randomized waiting-list controlled trial, 12-month follow-up", "randomized_controlled_trial",
             "human", "adults with moderate to severe major depression", 24, endpoint, "clinical", direction,
             quote, unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=25, dose_unit="mg/70 kg",
             route="oral", regimen="two doses with supportive psychotherapy", comp="baseline",
             comp_type="baseline_within_subject", arm_label="Psilocybin with psychotherapy",
             norm=norm, instrument="GRID-HAMD", section="Abstract", **kw)


D["PMC8864328"] = paper(
    "Twelve-month follow-up of psilocybin-assisted treatment for major depressive disorder.",
    [
        mdd12("GRID-HAMD depression score", "gridhamd_score", "decrease",
              "Large decreases from baseline in GRID-HAMD scores were observed at 1-, 3-, 6-, and 12-month follow-up (Cohen d = 2.3, 2.0, 2.6, and 2.4, respectively)",
              es=2.3, es_type="standardized_mean_difference", t=1, t_unit="months", t_origin="second dose",
              clinical=clin(scale="GRID-HAMD", higher="worse", blind="no", follow="1 month")),
        mdd12("GRID-HAMD depression score", "gridhamd_score", "decrease",
              "Large decreases from baseline in GRID-HAMD scores were observed at 1-, 3-, 6-, and 12-month follow-up (Cohen d = 2.3, 2.0, 2.6, and 2.4, respectively)",
              es=2.4, es_type="standardized_mean_difference", t=12, t_unit="months", t_origin="second dose",
              clinical=clin(scale="GRID-HAMD", higher="worse", blind="no", resp=0.75, remis=0.58,
                            resp_def="at least 50% reduction in GRID-HAMD from baseline", follow="12 months")),
        mdd12("Serious adverse events related to psilocybin", "serious_adverse_events", "no_change",
              "There were no serious adverse events judged to be related to psilocybin in the long-term follow-up period",
              value=0, vunit="events", t=12, t_unit="months", t_origin="second dose",
              clinical=clin(follow="12 months")),
    ])

# --- PMC7744693: psilocybin and sleep architecture (randomized double-blind crossover) -------------
def sleep(endpoint, norm, scale, direction, quote, **kw):
    return q("Randomized double-blind crossover sleep study", "randomized_controlled_trial", "human",
             "healthy volunteers aged 28-53", 20, endpoint, scale, direction, quote, unit="participant",
             drug="psilocybin", drug_norm="Psilocybin", route="oral", regimen="single session",
             comp="placebo", comp_type="placebo", arm_label="Psilocybin (dose not stated in abstract)",
             norm=norm, instrument="polysomnography", section="Abstract", t=1, t_unit="nights",
             t_origin="administration", **kw)


D["PMC7744693"] = paper(
    "Randomized crossover study of psilocybin effects on sleep architecture and EEG slow-wave activity.",
    [
        sleep("REM sleep latency", "rem_sleep_latency", "circuit", "increase",
              "The results revealed prolonged REM sleep latency after psilocybin administration",
              clinical=clin(follow="first night")),
    ])

# --- PMC7643385: psilocybin and self/other processing, EEG event-related potentials ----------------
D["PMC7643385"] = paper(
    "Placebo-controlled crossover EEG study of psilocybin effects on self-related auditory processing.",
    [
        q("Placebo-controlled double-blind crossover", "randomized_controlled_trial", "human",
          "healthy adults", 17, "Distinctiveness of self- vs other-related event-related potentials",
          "circuit", "decrease",
          "altered the late phase of self\u2010stimuli encoding by abolishing the distinctiveness of self\u2010 and other\u2010related electric",
          unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=230, dose_unit="\u00b5g/kg",
          route="oral", comp="placebo", comp_type="placebo", norm="erp_self_other_distinctiveness",
          instrument="EEG event-related potentials", section="Abstract"),
    ])

# --- PMC5813058: psilocybin and emotional face recognition in treatment-resistant depression --------
def face(endpoint, norm, direction, quote, **kw):
    return q("Open-label trial with non-treated control group", "open_label_trial", "human",
             "patients with treatment-resistant depression", 17, endpoint, "behavioral", direction, quote,
             unit="participant", drug="psilocybin", drug_norm="Psilocybin", route="oral",
             regimen="two doses with psychological support", comp="baseline",
             comp_type="baseline_within_subject", arm_label="Psilocybin (two doses)", norm=norm,
             instrument="dynamic emotional face recognition task", section="Abstract", **kw)


D["PMC5813058"] = paper(
    "Study of emotional face recognition speed before and after psilocybin in treatment-resistant depression.",
    [
        face("Speed of emotion recognition", "emotion_recognition_speed", "increase",
             "Emotion recognition was faster at follow-up compared with baseline in patients ( p = .004, d = .876) but not controls ( p = .263, d = .302)",
             es=0.876, es_type="standardized_mean_difference", p="0.004", t=1, t_unit="months",
             t_origin="treatment"),
        face("Group by time interaction on recognition speed", "emotion_recognition_interaction", "increase",
             "We found evidence for a group \u00d7 time interaction on speed of emotion recognition ( p = .035)",
             p="0.035", t=1, t_unit="months", t_origin="treatment"),
    ])

# --- PMC8032715: psilocybin and creative thinking (double-blind parallel group) --------------------
def creat(endpoint, norm, direction, quote, t, t_unit, **kw):
    return q("Double-blind placebo-controlled parallel group", "randomized_controlled_trial", "human",
             "healthy participants", None, endpoint, "behavioral", direction, quote, unit="participant",
             drug="psilocybin", drug_norm="Psilocybin", dose=0.17, dose_unit="mg/kg", route="oral",
             comp="placebo", comp_type="placebo", norm=norm, instrument="creativity tasks and ratings",
             section="Abstract", t=t, t_unit=t_unit, t_origin="administration", **kw)


D["PMC8032715"] = paper(
    "Placebo-controlled study of acute and persisting psilocybin effects on creative thinking.",
    [
        creat("Ratings of spontaneous creative insights", "spontaneous_creative_insight", "increase",
              "Acutely, psilocybin increased ratings of (spontaneous) creative insights, while decreasing (deliberate) task-based creativity",
              1, "days"),
        creat("Task-based (deliberate) creativity", "deliberate_creativity", "decrease",
              "Acutely, psilocybin increased ratings of (spontaneous) creative insights, while decreasing (deliberate) task-based creativity",
              1, "days"),
        creat("Number of novel ideas", "novel_ideas", "increase",
              "Seven days after psilocybin, number of novel ideas increased", 7, "days"),
    ])

# --- PMC5581487: psilocybin and empathy / moral decision-making ------------------------------------
def emp(endpoint, norm, direction, quote, n, **kw):
    return q("Placebo-controlled study in healthy subjects", "randomized_controlled_trial", "human",
             "healthy adults", n, endpoint, "behavioral", direction, quote, unit="participant",
             drug="psilocybin", drug_norm="Psilocybin", dose=0.215, dose_unit="mg/kg", route="oral",
             comp="placebo", comp_type="placebo", norm=norm, section="Abstract", **kw)


D["PMC5581487"] = paper(
    "Placebo-controlled study of acute psilocybin effects on empathy and moral decision-making.",
    [
        emp("Emotional empathy", "emotional_empathy", "increase",
            "Psilocybin significantly increased emotional, but not cognitive empathy compared with placebo", 32,
            instrument="multifaceted empathy test"),
        emp("Cognitive empathy", "cognitive_empathy", "no_change",
            "Psilocybin significantly increased emotional, but not cognitive empathy compared with placebo", 32,
            instrument="multifaceted empathy test"),
        emp("Moral decision-making", "moral_decision_making", "no_change",
            "In contrast, moral decision-making remained unaffected by psilocybin", 24,
            instrument="moral dilemma task"),
    ])

# --- PMC6220878: psilocybin therapy and personality structure --------------------------------------
def pers(endpoint, norm, direction, quote, **kw):
    return q("Open-label trial", "open_label_trial", "human",
             "patients with treatment-resistant depression", 20, endpoint, "behavioral", direction, quote,
             unit="participant", drug="psilocybin", drug_norm="Psilocybin", dose=25, dose_unit="mg",
             route="oral", regimen="10 mg then 25 mg, one week apart", comp="baseline",
             comp_type="baseline_within_subject", arm_label="Psilocybin (10 mg then 25 mg)", norm=norm,
             instrument="NEO-PI-R", t=3, t_unit="months", t_origin="treatment", section="Abstract", **kw)


D["PMC6220878"] = paper(
    "Open-label study of personality change measured by NEO-PI-R after psilocybin therapy for depression.",
    [
        pers("Neuroticism score", "neuroticism", "decrease",
             "Neuroticism scores significantly decreased while Extraversion increased following psilocybin therapy"),
        pers("Extraversion score", "extraversion", "increase",
             "Neuroticism scores significantly decreased while Extraversion increased following psilocybin therapy"),
        pers("Openness score", "openness", "increase",
             "Openness scores also significantly increased following psilocybin, whereas Conscientiousness showed trend\u2010level increases, and Agreeableness did not change"),
        pers("Agreeableness score", "agreeableness", "no_change",
             "Openness scores also significantly increased following psilocybin, whereas Conscientiousness showed trend\u2010level increases, and Agreeableness did not change"),
    ])

# --- PMC7359647: retrospective survey of ibogaine + 5-MeO-DMT program in veterans -------------------
def vetsurvey(endpoint, norm, scale, direction, quote, es, **kw):
    return q("Retrospective survey of a psychedelic program", "survey", "human",
             "US Special Operations Forces veterans", 51, endpoint, scale, direction, quote, unit="participant",
             drug="ibogaine and 5-MeO-DMT", drug_norm="Ibogaine + 5-MeO-DMT",
             regimen="combined ibogaine and 5-MeO-DMT program",
             comp="retrospective report of the 30 days before treatment", comp_type="baseline_within_subject",
             arm_label="Ibogaine + 5-MeO-DMT program", norm=norm, es=es,
             es_type="standardized_mean_difference", p="<0.001", instrument="retrospective self-report",
             t=30, t_unit="days", t_origin="treatment", section="Abstract", **kw)


D["PMC7359647"] = paper(
    "Retrospective survey of veterans reporting symptoms before and after a combined ibogaine and 5-MeO-DMT program.",
    [
        vetsurvey("Suicidal ideation (retrospective report)", "suicidal_ideation", "clinical", "decrease",
                  "significant and very large reductions in retrospective report of suicidal ideation (p < .001; d = \u22121.9)",
                  -1.9, clinical=clin(higher="worse", follow="30 days after")),
        vetsurvey("PTSD symptoms (retrospective report)", "ptsd_symptoms", "clinical", "decrease",
                  "symptoms of posttraumatic stress disorder (p < .001; d = \u22123.6)", -3.6,
                  clinical=clin(higher="worse", follow="30 days after")),
        vetsurvey("Depression symptoms (retrospective report)", "depression_symptoms", "clinical", "decrease",
                  "depression (p < .001; d = \u22123.7)", -3.7, clinical=clin(higher="worse", follow="30 days after")),
        vetsurvey("Cognitive impairment (retrospective report)", "cognitive_impairment", "behavioral", "decrease",
                  "cognitive impairment (p < .001; d = \u22122.8)", -2.8),
        vetsurvey("Psychological flexibility (retrospective report)", "psychological_flexibility", "behavioral",
                  "increase",
                  "a significant and large increase in retrospective report of psychological flexibility (p < .001; d = 2.9)",
                  2.9),
    ])

# --- Papers with no new measured outcomes ----------------------------------------------------------
D["PMC4828992"] = none("Narrative review of DMT in neuroinflammation and neuroprotection; no new measurements.")
D["PMC3800812"] = none("Theoretical review of serotonergic hyperactivity and synesthesia; no new measurements.")
D["PMC5776504"] = none("Secondary analysis of acute experience ratings predicting outcomes in an already-extracted trial (PMC5813086); no new measured outcomes.")
D["PMC6194345"] = none("Task-based analysis of pessimism bias in an already-extracted trial cohort; reports prediction-task indices rather than new intervention outcomes.")
D["PMC4589238"] = none("EEG study of ayahuasca (a DMT-containing brew) reporting spectral power changes; the study substance is ayahuasca, not isolated DMT, so it is kept as contextual evidence only.")

if __name__ == "__main__":
    write(D, sys.argv[1])
