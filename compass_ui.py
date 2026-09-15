"""AI × Open Science Compass: twelve questions, two axes, one conversation.

Nothing here judges anyone. The scoring is shown in full on the same page as
the result, so a participant can disagree with the instrument as easily as
with their own answers.
"""
import json
from datetime import datetime, timezone

import plotly.graph_objects as go
import streamlit as st

from compass_engine import (ARCHETYPES, AXES, BAND_EDGES, CHOICES, KEYS,
                            MINIMUM_ANSWERS, QUESTIONS, VERSION, sanitize, score)
from theme import PALETTE, footer, note, page_header, score_bar, source_files

# The build script rewrites this to () for the generated single-file app.
SOURCE_FILES = ("compass_engine.py",)

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
