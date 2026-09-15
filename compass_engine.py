"""An original workshop reflection instrument, inspired by The AI Compass.

This is not a validated psychological scale and must not be used to evaluate
people. The historical names are fictional mnemonics for nine regions of a
two-axis diagram; they are not claims about those historians' views.

Every design choice below is deliberate and inspectable: six items per axis,
two reverse-keyed items, a minimum of four answers per axis, and three equal
bands. Skipping is never scored as disagreement.
"""
QUESTIONS = [
    ("O1", "open", False, "My next paper includes reusable data and code, with an explicit licence, wherever sharing is ethical and lawful."),
    ("A1", "ai", False, "I would use AI to propose several hypotheses before choosing which to test."),
    ("O2", "open", True, "A PDF and a methods paragraph are usually enough; sharing an executable workflow adds little value."),
    ("A2", "ai", False, "I would use AI to draft analysis code if I can inspect it and test it against known cases."),
    ("O3", "open", False, "I would publish failed approaches and consequential deviations from my original plan."),
    ("A3", "ai", True, "Even after independent checks, I would avoid AI-generated contributions to my research."),
    ("O4", "open", False, "I would share a reusable method early, even if another group might build on it before my main paper appears."),
    ("A4", "ai", False, "I would use AI to triage a large literature or dataset, then audit a sample and all important claims."),
    ("O5", "open", False, "I would make the provenance of a result inspectable, including relevant tool versions and human decisions."),
    ("A5", "ai", False, "I would routinely invite AI criticism of my own shareable manuscript before submission."),
    ("O6", "open", False, "I would invest time in documentation, open standards and community contributions, even if they earn fewer publication credits."),
    ("A6", "ai", False, "I would delegate a bounded research task to an AI agent with an agreed goal, a resource limit and human approval of consequential actions."),
]
CHOICES = ["Strongly disagree", "Disagree", "Mixed / depends", "Agree", "Strongly agree"]
AXES = {
    "open": ("Open Science", "Guarded", "Open by design"),
    "ai": ("AI assistance", "Limited use", "Extensive assistance"),
}
VERSION = "1.1.0"
MINIMUM_ANSWERS = 4
BAND_EDGES = (100 / 3, 200 / 3)
KEYS = tuple(question[0] for question in QUESTIONS)

ARCHETYPES = {
    (0, 0): ("The Newton Study", "Guarded exploration with strong personal control."),
    (1, 0): ("The Darwin Notebook", "Selective sharing and a preference for direct human investigation."),
    (2, 0): ("The Curie Laboratory", "Open sharing of methods, with limited AI delegation."),
    (0, 1): ("The Edison Workshop", "Selective automation inside a controlled research process."),
    (1, 1): ("The Leonardo Studio", "A context-dependent balance of openness and AI assistance."),
    (2, 1): ("The Gutenberg Commons", "Broad access with selective use of AI tools."),
    (0, 2): ("The von Neumann Engine", "Extensive AI assistance with guarded sharing."),
    (1, 2): ("The Turing Laboratory", "Extensive AI assistance with negotiated openness."),
    (2, 2): ("The Ada Lovelace Commons", "Extensive AI assistance and open, reusable research."),
}


def band(value):
    """Map a 0-100 axis score onto one of three equal bands: 0, 1 or 2."""
    return 0 if value < BAND_EDGES[0] else 2 if value >= BAND_EDGES[1] else 1


def valid_answer(value):
    """True for a whole number 0-4. Booleans are rejected on purpose."""
    return isinstance(value, int) and not isinstance(value, bool) and value in range(5)


def sanitize(answers):
    """Return a clean answer dictionary: known keys only, 0-4 or None.

    A browser session can outlive a redeployment, so the app may be handed
    answers recorded by an older version of this file. Anything unrecognised
    becomes a skip rather than an error on a participant's screen.
    """
    if not isinstance(answers, dict):
        return {}
    return {key: answers[key] for key in KEYS
            if key in answers and (answers[key] is None or valid_answer(answers[key]))}


def score(answers):
    """Score both axes from 0 to 100, or None where too little was answered.

    Reverse-keyed items are recoded as 4 - answer. Each axis is 25 times the
    mean of its answered items, which puts a mid-scale response at 50. Skips
    are excluded from the mean, never counted as zero.
    """
    if not isinstance(answers, dict):
        raise ValueError("Answers must be a dictionary of question keys")
    for key, value in answers.items():
        if value is not None and not valid_answer(value):
            raise ValueError("Answers must be integers 0-4 or None")
    result = {}
    for axis in AXES:
        values = [4 - answers[key] if reverse else answers[key]
                  for key, question_axis, reverse, _ in QUESTIONS
                  if question_axis == axis and answers.get(key) is not None]
        result[axis + "_answered"] = len(values)
        result[axis] = (round(25 * sum(values) / len(values), 1)
                        if len(values) >= MINIMUM_ANSWERS else None)
    result["complete"] = all(answers.get(key) is not None for key in KEYS)
    result["instrument_version"] = VERSION
    if result["open"] is not None and result["ai"] is not None:
        cell = (band(result["open"]), band(result["ai"]))
        result["cell"] = list(cell)
        result["archetype"], result["description"] = ARCHETYPES[cell]
    return result
