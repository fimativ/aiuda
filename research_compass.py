"""AI × Open Science Compass — Sinuhé Perea · OSA / MPG · 15 September 2026.

Run:     python3 -m streamlit run research_compass.py
Install: python3 -m pip install 'streamlit>=1.58,<2' 'plotly>=5.17,<7'

GENERATED FILE — do not edit by hand. It is assembled from theme.py, compass_engine.py, compass_ui.py
by build_standalone.py, so this activity and the combined app.py always run
identical logic. Edit those modules and run `python3 build_standalone.py`.

This file contains the activity and its complete calculation logic. No
companion Python modules, AI API keys or remote services are required. Keep
.streamlit/config.toml alongside it for the black and green workshop theme.
Public hosting runs this code on the host, not only in the participant's
browser. Original workshop code: MIT licence. See the accompanying LICENSE.
"""

import json
import plotly.graph_objects as go
import streamlit as st

from datetime import datetime, timezone
from pathlib import Path
from string import Template


# ========================================================================
# theme.py
# ========================================================================

PALETTE = {
    "ink": "#000000",          # page canvas, matching the projected slides
    "panel": "#0B1512",        # raised surface
    "panel_soft": "#101B19",   # secondary surface, as in .streamlit/config.toml
    "line": "#1E3430",         # hairline borders
    "line_soft": "#152623",
    "green": "#007367",        # Max Planck green, the primary accent
    "green_bright": "#55CBB2",
    "green_pale": "#9EF2D6",
    "text": "#F4F7F6",
    "muted": "#93A9A3",
    "dim": "#6A807A",
    "square_dark": "#162A25",
    "square_light": "#3C564E",
    "amber": "#E0B25C",        # used only for cautions
}

STYLESHEET = Template("""
<style>
/* ---- page shell ------------------------------------------------------- */
.block-container{max-width:1180px;padding-top:2.1rem;padding-bottom:4.5rem}
header[data-testid=stHeader]{background:$ink}
h1,h2,h3,h4{font-weight:500!important;letter-spacing:-.011em}
h1{font-size:2.45rem!important;line-height:1.12!important;margin-bottom:.15rem!important}
h2{font-size:1.5rem!important} h3{font-size:1.18rem!important}
a{color:$green_bright;text-decoration:none;border-bottom:1px solid rgba(85,203,178,.3)}
a:hover{border-bottom-color:$green_bright}
hr{border-color:$line_soft}

/* ---- page header ------------------------------------------------------ */
.st-key-pagehead [data-testid=stElementContainer]{margin-bottom:0}
.st-key-pagehead h1{margin-top:.1rem!important}
.osa-kicker{font-size:.7rem;letter-spacing:.19em;text-transform:uppercase;
  color:$green_bright;font-weight:600;display:flex;align-items:center;gap:.7rem}
.osa-kicker:after{content:"";flex:1;height:1px;
  background:linear-gradient(90deg,$line 0%,rgba(30,52,48,0) 100%)}
.osa-lede{color:$muted;font-size:1.02rem;line-height:1.55;max-width:62ch;margin:.55rem 0 0}

/* ---- surfaces --------------------------------------------------------- */
[data-testid=stVerticalBlockBorderWrapper]{border-radius:10px}
.osa-card{background:$panel;border:1px solid $line;border-radius:10px;padding:1rem 1.15rem}
.osa-note{border-left:2px solid $green;background:$panel_soft;border-radius:0 8px 8px 0;
  padding:.7rem .95rem;color:$muted;font-size:.88rem;line-height:1.55}

/* ---- controls --------------------------------------------------------- */
.stButton button{border-radius:7px;font-weight:450;transition:transform .08s ease,
  border-color .12s ease,background .12s ease}
.stButton button:hover{transform:translateY(-1px)}
[data-testid=stMetricValue]{font-size:3.4rem;color:$green_bright;font-weight:300;
  line-height:1.05;font-variant-numeric:tabular-nums}
[data-testid=stMetricLabel] p{font-size:.72rem!important;letter-spacing:.17em;
  text-transform:uppercase;color:$muted!important}
[data-testid=stSidebarUserContent]{padding-top:1.6rem}
section[data-testid=stSidebar]{border-right:1px solid $line_soft}

/* ---- board ------------------------------------------------------------ */
/* The squares take their size from the column width and stay square at any
   window size, so the board never stretches into rectangles. */
[class*="st-key-square_"] button{aspect-ratio:1;height:auto;min-height:0;width:100%;
  padding:0;border-radius:2px;border:1px solid $ink;color:$text!important;
  text-shadow:0 1px 3px rgba(0,0,0,.7);transition:filter .1s ease}
[class*="st-key-square_"] button:hover{filter:brightness(1.4);transform:none;
  border-color:$green_bright!important;z-index:2}
[class*="st-key-square_"] button:focus:not(:active){border-color:$green_bright!important}
[class*="st-key-square_"] button p{font-size:clamp(20px,2.4vw,30px)!important;
  line-height:1!important}
/* .st-key-boardgrid is itself the flex container that stacks the eight ranks. */
.st-key-boardgrid{gap:0!important}
.st-key-boardgrid [data-testid=stElementContainer]{margin-bottom:0}
.st-key-boardgrid [data-testid=stHorizontalBlock]{gap:0!important}
/* On a narrow screen Streamlit stacks columns by giving each one a full-width
   minimum. A chessboard must stay eight across on a phone, so the board grid
   opts out of that and lets its squares shrink instead. */
.st-key-boardgrid [data-testid=stHorizontalBlock]{flex-wrap:nowrap!important}
.st-key-boardgrid [data-testid=stColumn]{min-width:0!important}
.osa-coord{color:$dim;font-size:.72rem;font-weight:600;letter-spacing:.06em;
  text-align:center;line-height:1.2;font-variant-numeric:tabular-nums}
.osa-coord-file{padding-top:.45rem}

/* ---- likert scale ----------------------------------------------------- */
/* Streamlit centres the label in an inner flex wrapper, so left alignment has
   to be set there as well as on the button itself. */
[class*="st-key-answer_"] button{padding-left:1rem;border-left-width:3px}
[class*="st-key-answer_"] button > div{width:100%;justify-content:flex-start;
  text-align:left}
.osa-dots{display:flex;gap:5px;margin:.1rem 0 .9rem}
.osa-dot{height:4px;flex:1;border-radius:2px;background:$line}
.osa-dot.done{background:$green} .osa-dot.now{background:$green_bright}
.osa-dot.skip{background:$dim}

/* ---- score bars ------------------------------------------------------- */
.osa-bar-row{margin:.85rem 0}
.osa-bar-top{display:flex;justify-content:space-between;font-size:.78rem;
  color:$muted;margin-bottom:.32rem}
.osa-bar-top b{color:$text;font-weight:500;font-variant-numeric:tabular-nums}
.osa-bar{height:7px;border-radius:4px;background:$panel_soft;
  border:1px solid $line_soft;overflow:hidden}
.osa-bar span{display:block;height:100%;
  background:linear-gradient(90deg,$green 0%,$green_bright 100%)}

/* ---- small print ------------------------------------------------------ */
.osa-foot{color:$dim;font-size:.78rem;line-height:1.6;border-top:1px solid $line_soft;
  padding-top:.85rem;margin-top:2.4rem}
</style>
""").substitute(PALETTE)

ABOUT = (
    "Workshop activities for *What AI Can (Un)veil for Open Science*. "
    "Sinuhé Perea, OSA / MPG Open Science community, 15 September 2026. "
    "No AI model is called and no answer database is created."
)


def page_setup(page_title):
    """Configure the page once and inject the shared stylesheet."""
    st.set_page_config(page_title=page_title, page_icon="◐", layout="wide",
                       menu_items={"About": ABOUT})
    st.html(STYLESHEET)


def page_header(kicker, title, lede):
    """A kicker rule, a title and one line of orientation, tightly spaced."""
    with st.container(key="pagehead"):
        st.html(f'<div class="osa-kicker">{kicker}</div>')
        st.title(title)
        st.html(f'<p class="osa-lede">{lede}</p>')


def sidebar_identity():
    """The same authorship block on every entry point."""
    st.sidebar.html(
        '<div class="osa-kicker" style="margin-bottom:.7rem">TRUE</div>'
        '<div style="color:%(muted)s;font-size:.84rem;line-height:1.75">'
        'Transparent<br>Reproducible<br>Usable by others<br>Extensible</div>'
        '<div style="height:1px;background:%(line)s;margin:1.15rem 0"></div>'
        '<div style="color:%(dim)s;font-size:.78rem;line-height:1.6">'
        'Sinuhé Perea<br>OSA / MPG Open Science<br>15 September 2026</div>' % PALETTE)


def note(text):
    """A quiet aside that is easy to skip and easy to find again."""
    st.html(f'<div class="osa-note">{text}</div>')


def score_bar(label, value, left, right):
    """A labelled 0-100 bar; value may be None when too little was answered."""
    shown = "—" if value is None else f"{value:g}"
    width = 0 if value is None else max(0.0, min(100.0, float(value)))
    st.html(f'<div class="osa-bar-row"><div class="osa-bar-top">'
            f'<span>{label} · {left} → {right}</span><b>{shown}<span '
            f'style="color:{PALETTE["dim"]}">/100</span></b></div>'
            f'<div class="osa-bar"><span style="width:{width}%"></span></div></div>')


def footer(*lines):
    """Small print, set apart by a hairline rather than by shouting."""
    st.html('<div class="osa-foot">' + "<br>".join(lines) + "</div>")


def source_files(*names):
    """Return {filename: source text} for the modules behind this app.

    In the modular layout this finds the named sibling modules. In a generated
    single-file build those modules do not exist, so the file being executed is
    returned instead. Either way the audience can read exactly what ran.
    """
    here = Path(__file__).resolve()
    found = {}
    for filename in names:
        candidate = here.with_name(filename)
        try:
            found[filename] = candidate.read_text(encoding="utf-8")
        except OSError:
            pass
    if not found:
        try:
            found[here.name] = here.read_text(encoding="utf-8")
        except OSError:
            found["source"] = "The source file could not be read from disk."
    return found


# ========================================================================
# compass_engine.py
# ========================================================================

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


# ========================================================================
# compass_ui.py
# ========================================================================

# The build script rewrites this to () for the generated single-file app.
SOURCE_FILES = ()

TOTAL = len(QUESTIONS)
SCALE_ACCENTS = ("#2A3B37", "#35564E", "#3F7A6C", "#4AA08A", "#55CBB2")
SCORING_NOTE = (
    f"Six questions per axis. Strongly disagree = 0, then 1, 2, 3, 4. "
    f"Reverse O2 and A3 as 4 − answer. Each axis is 25 × its mean answered "
    f"score, so a mid-scale response gives 50. At least {MINIMUM_ANSWERS} answers "
    f"per axis are required. The three bands are below 33⅓, 33⅓ to below 66⅔, "
    f"and 66⅔ or higher. Skips are excluded and never counted as disagreement. "
    f"These cutoffs are workshop design choices, not measurements."
)


# --------------------------------------------------------------------------
# session state
# --------------------------------------------------------------------------
def _sanitize_state():
    """Keep the three pieces of state consistent, whatever arrives in them."""
    state = st.session_state
    state.answers = sanitize(state.get("answers"))
    question = state.get("question")
    if not isinstance(question, int) or isinstance(question, bool):
        question = 0
    state.question = max(0, min(TOTAL - 1, question))
    state.show_result = bool(state.get("show_result", False))
    state.reviewing = bool(state.get("reviewing", False))


def _advance():
    """Move to the next question, or to the result after the last one."""
    if st.session_state.question >= TOTAL - 1:
        st.session_state.show_result = True
        st.session_state.reviewing = False
    else:
        st.session_state.question += 1
    st.rerun()


def _restart():
    st.session_state.answers = {}
    st.session_state.question = 0
    st.session_state.show_result = False
    st.session_state.reviewing = False
    st.rerun()


# --------------------------------------------------------------------------
# the questionnaire
# --------------------------------------------------------------------------
def _progress_dots(current):
    """Twelve marks: answered, skipped, current, not yet reached."""
    marks = []
    for index, key in enumerate(KEYS):
        if index == current:
            marks.append("now")
        elif key not in st.session_state.answers:
            marks.append("")
        else:
            marks.append("done" if st.session_state.answers[key] is not None else "skip")
    st.html('<div class="osa-dots">'
            + "".join(f'<div class="osa-dot {m}"></div>' for m in marks)
            + "</div>")


def _question():
    index = st.session_state.question
    key, axis, reverse, prompt = QUESTIONS[index]
    saved = st.session_state.answers.get(key)
    answered = key in st.session_state.answers and saved is not None

    top, counter = st.columns([3, 1], vertical_alignment="bottom")
    top.caption(f"Question {index + 1} of {TOTAL} · {AXES[axis][0]}"
                + ("  ·  reverse-keyed" if reverse else ""))
    counter.caption(f"{sum(1 for k in KEYS if k in st.session_state.answers)}"
                    f"/{TOTAL} seen")
    _progress_dots(index)
    st.subheader(prompt)

    # The scale runs down the page, so its order is carried by a left edge that
    # brightens with agreement rather than by left-and-right anchor labels.
    st.html("<style>" + "".join(
        f".st-key-answer_{key}_{value} button{{border-left-color:{accent}!important}}"
        for value, accent in enumerate(SCALE_ACCENTS)) + "</style>")
    for value, label in enumerate(CHOICES):
        chosen = saved == value
        if st.button(label + ("  ✓" if chosen else ""), key=f"answer_{key}_{value}",
                     width="stretch", type="primary" if chosen else "secondary"):
            st.session_state.answers[key] = value
            _advance()

    st.html("<div style='height:.5rem'></div>")
    back, forward, clear = st.columns(3)
    if back.button("Back", disabled=index == 0, width="stretch", key="nav_back"):
        st.session_state.question = index - 1
        st.rerun()
    # Advancing must never silently erase an answer, so a saved answer turns
    # the skip control into a plain Next and offers clearing as its own step.
    if forward.button("Next" if answered else "Skip", width="stretch", key="nav_next"):
        if not answered:
            st.session_state.answers[key] = None
        _advance()
    if clear.button("Clear answer", disabled=not answered, width="stretch",
                    key="nav_clear"):
        st.session_state.answers[key] = None
        st.rerun()
    if st.session_state.reviewing:
        if st.button("Back to my result", width="stretch", key="nav_result"):
            st.session_state.show_result = True
            st.session_state.reviewing = False
            st.rerun()
    st.caption("Skipping is not disagreement. Skipped questions are left out of "
               "the mean rather than scored as zero.")


# --------------------------------------------------------------------------
# the diagram
# --------------------------------------------------------------------------
def compass_figure(result=None):
    """The nine regions, with the participant's position when there is one."""
    here = tuple(result["cell"]) if result and "cell" in result else None
    figure = go.Figure()
    for (x, y), (title, _) in ARCHETYPES.items():
        current = here == (x, y)
        # Plotly draws shapes above traces by default, which would bury the
        # participant's marker underneath these nine rectangles.
        figure.add_shape(
            type="rect", x0=x * 100 / 3, y0=y * 100 / 3,
            x1=(x + 1) * 100 / 3, y1=(y + 1) * 100 / 3, layer="below",
            fillcolor=["#0D201C", "#16372F", "#205245"][(x + y) // 2],
            line=dict(color=PALETTE["green_bright"] if current else "#315448",
                      width=2 if current else 1))
        figure.add_annotation(
            x=(x + .5) * 100 / 3, y=(y + .5) * 100 / 3,
            text=title.replace("The ", "").replace(" ", "<br>", 1), showarrow=False,
            font=dict(size=12, color=PALETTE["text"] if current else "#8FA7A0"))
    for edge in BAND_EDGES:
        for line in (dict(x0=edge, x1=edge, y0=0, y1=100),
                     dict(x0=0, x1=100, y0=edge, y1=edge)):
            figure.add_shape(type="line", layer="below", **line,
                             line=dict(color="#0A1614", width=1))
    if result and result.get("open") is not None and result.get("ai") is not None:
        # A score near either end would push the label off the diagram, so it
        # is placed on whichever side has room.
        on_the_right = result["open"] > 50
        figure.add_trace(go.Scatter(
            x=[result["open"]], y=[result["ai"]], mode="markers+text",
            marker=dict(size=18, color="#FFFFFF",
                        line=dict(color=PALETTE["ink"], width=6)),
            text=["you are here  " if on_the_right else "  you are here"],
            textposition="middle left" if on_the_right else "middle right",
            textfont=dict(color="#FFFFFF", size=13), name="You",
            hovertemplate="Open Science %{x}<br>AI assistance %{y}<extra></extra>"))
    axis = dict(range=[-4, 104], fixedrange=True, showgrid=False, zeroline=False,
                tickvals=[0, 100 / 3, 200 / 3, 100], ticktext=["0", "33", "67", "100"],
                tickfont=dict(color=PALETTE["dim"], size=11),
                title_font=dict(color=PALETTE["muted"], size=12))
    figure.update_layout(
        height=520, paper_bgcolor=PALETTE["ink"], plot_bgcolor=PALETTE["ink"],
        margin=dict(l=52, r=24, t=16, b=52), showlegend=False,
        xaxis=dict(title="OPEN SCIENCE · guarded → open by design", **axis),
        yaxis=dict(title="AI · limited use → extensive assistance", **axis))
    return figure


# --------------------------------------------------------------------------
# the result
# --------------------------------------------------------------------------
def _result():
    result = score(st.session_state.answers)
    located = "archetype" in result
    summary, diagram = st.columns([1, 1.25], gap="large")

    with summary:
        if located:
            st.caption("Your region")
            st.subheader(result["archetype"])
            st.write(result["description"])
        else:
            st.subheader("Not enough answers yet")
            st.info(f"Answer at least {MINIMUM_ANSWERS} questions on each axis to "
                    "be placed on the diagram. Skips are never read as disagreement.")
        for axis, (label, low, high) in AXES.items():
            score_bar(label, result[axis], low, high)
        st.caption(f"Answered: {AXES['open'][0]} {result['open_answered']}/6 · "
                   f"{AXES['ai'][0]} {result['ai_answered']}/6. "
                   "No uncertainty interval is estimated.")
        if located:
            note("<b>Discuss with a neighbour:</b> which answer would change in "
                 "another project? What one practice would make your next result "
                 "easier for someone else to inspect?")

    with diagram:
        st.plotly_chart(compass_figure(result if located else None),
                        width="stretch", config={"displayModeBar": False},
                        key="result_compass")

    review, restart = st.columns(2)
    if review.button("Review or change my answers", width="stretch", key="review"):
        st.session_state.question = 0
        st.session_state.show_result = False
        st.session_state.reviewing = True
        st.rerun()
    if restart.button("Start again", width="stretch", key="restart"):
        _restart()
    st.download_button(
        "Download my answers and scoring",
        json.dumps({"instrument": "OSA Compass",
                    "instrument_version": VERSION,
                    "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "choices": CHOICES,
                    "answers": {key: st.session_state.answers.get(key) for key in KEYS},
                    "result": result}, indent=2, ensure_ascii=False),
        "my_research_compass.json", "application/json", width="stretch")


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------
def render():
    """Draw the whole activity. Safe to call on every rerun."""
    _sanitize_state()
    page_header("Activity two", "AI × Open Science",
                "Twelve questions on two independent axes. A conversation "
                "starter, not a measurement of anybody.")
    st.divider()
    if st.session_state.show_result:
        _result()
    else:
        _question()

    with st.expander("The scoring is open"):
        st.markdown(SCORING_NOTE)
        st.dataframe([{"ID": key, "Axis": AXES[axis][0], "Reverse": reverse,
                       "Question": prompt} for key, axis, reverse, prompt in QUESTIONS],
                     hide_index=True, width="stretch")
        st.plotly_chart(compass_figure(), width="stretch",
                        config={"displayModeBar": False}, key="blank_compass")
        for filename, text in source_files(*SOURCE_FILES).items():
            st.caption(filename)
            st.code(text, language="python")

    footer("Historical names are fictional mnemonic labels, not measured views, "
           "endorsements or personality diagnoses. This unvalidated instrument "
           "must not be used to evaluate people.",
           'Inspired by <a href="https://bambamramfan.github.io/ai-compass/">'
           "The AI Compass</a>. Original questions, axes and scoring for this workshop.",
           "No names, email addresses, AI API calls or answer database. Answers "
           "remain in the server session until it ends or you reset them. A hosting "
           "provider may retain ordinary access logs. Do not enter confidential "
           "information.")


# ========================================================================
# entry point
# ========================================================================

page_setup("AI × Open Science Compass")
sidebar_identity()
render()
