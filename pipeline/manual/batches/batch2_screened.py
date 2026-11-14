"""Batch 2: papers screened out (no new measured outcomes), hand-screened in a Claude Code session."""
import sys

sys.path.insert(0, "..")
from helpers import none, write  # noqa: E402

D = {
    "PMC4464176": none("Theoretical article applying integrated information theory to the psychedelic state; no new measurements."),
    "PMC6137697": none("Conceptual review linking meditation and psychedelics; no new measurements."),
    "PMC5584001": none("Qualitative thematic analysis of online forum posts; no measured outcomes against a comparator."),
    "PMC4944667": none("Pharmacokinetic modeling and simulation proposal for DMT infusion; no measured intervention outcomes."),
    "PMC7196827": none("Computational whole-brain modeling of existing imaging data; reports model fits, not new measured outcomes."),
    "PMC7908919": none("Description of a therapist training program; no measured outcomes."),
    "PMC5893695": none("Mainly qualitative interview analysis of music in therapy; no measured outcomes against a comparator."),
    "PMC5891594": none("Case narratives of four patients from a previously published trial; outcomes re-reported, not new."),
}

if __name__ == "__main__":
    write(D, sys.argv[1])
