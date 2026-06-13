"""Mutable configuration surface for the OpenMontage autoresearch loop.

Autonomous optimization agents may edit only the constants in this file.
The evaluator in ``prepare.py`` imports these values and produces a Structural
Dissimilarity Score (SDS); lower is better.
"""

# Visual structure controls. Keep values numeric and JSON-serializable.
MOTION_DENSITY = 0.58
CUT_RHYTHM = 0.61
EVIDENCE_CARD_SCALE = 0.44
TYPOGRAPHY_WEIGHT = 0.62
CONTRAST_BALANCE = 0.68
TEAL_ACCENT_STRENGTH = 0.49
ARCHIVAL_NOISE = 0.18
LOWER_THIRD_DISCIPLINE = 0.73
