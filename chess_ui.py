"""MiniChess: place targets, read two numbers, then open the instruction book.

Round 1 shows only the outputs A and B. Round 2 names the pieces, states the
rules, replays a shortest route and offers the solver's source. The point of
the activity is the distance between watching an output and auditing a method.
"""
import json
import random
from datetime import datetime, timezone

import plotly.graph_objects as go
import streamlit as st

from chess_engine import (MAX_TARGETS, PIECES, name, on_board, solve, square,
                          verify)
from theme import PALETTE, footer, note, page_header, source_files

# The build script rewrites this to () for the generated single-file app,
# so each build shows the audience exactly the file that is running.
SOURCE_FILES = ("chess_engine.py",)

SYMBOLS = ["♟", "♜", "♞", "♝", "♛"]
ACTIONS = ["Place a target", "Erase", "Move the start square"]
DEFAULT_SEED = 150926

# Every preset is one of the boards shown on the slides. The pairs in the
# captions are (rook, knight) and are reproduced by the solver, not typed in.
EXAMPLES = {
    "2 in a row": ("a1", ["b1", "c1"]),
    "3 in a row": ("a1", ["b1", "c1", "d1"]),
    "4 in a row": ("a1", ["b1", "c1", "d1", "e1"]),
    "3 diagonal": ("a1", ["b2", "c3", "d4"]),
}

RULES = """
### The instruction book

**The highlighted square is the starting square**, not a chess check.
Run two separate trials on the same board: one rook and one knight.
All placed chess symbols are stationary targets. Their type is decoration;
they do not move, attack, give check or have different values.

* A rook moves any positive number of squares along one row or column.
  It cannot jump over a target. It can land on the first target and capture it.
* A knight jumps in an L: two squares in one direction, one perpendicular.
  It can jump over targets and captures only on its landing square.
* A capture removes that target. Empty-square moves are allowed and count.
* One move costs one, regardless of distance. Capture every target.
* Both trials restart from the original board. No kings, turns, check,
  checkmate, promotion, castling, opponent or return-to-start requirement.
* Up to eight targets keeps the exact search suitable for a live workshop.
  The empty board has score zero for both pieces.

**A is the rook minimum. B is the knight minimum.** We do not sort the outputs.
The smaller number need not equal the number of targets.

### Why the minimum is exact

Breadth-first search explores every state reachable in 0 moves, then 1,
then 2, and so on, until all targets have been captured. A state records
the current square and which targets remain. Every legal move costs one.
The first finished state therefore has minimum length. An independent
replay checks its legal steps. A replay alone would not prove optimality.

This is a deterministic algorithm, not an AI model. It illustrates the
difference between observing an output and auditing its method.
"""


# --------------------------------------------------------------------------
# session state
# --------------------------------------------------------------------------
def _sanitize_state():
    """Repair anything unusable in session state instead of crashing on it.

    A browser session can outlive a redeployment, so this code may be handed
    a board recorded by an earlier version of the app.
    """
    state = st.session_state
    start = state.get("start")
    if not on_board(start):
        start = square("e4")
    targets = state.get("targets")
    if not isinstance(targets, dict):
        targets = {}
    clean = {cell: symbol for cell, symbol in targets.items()
             if on_board(cell) and cell != start and symbol in SYMBOLS}
    if len(clean) > MAX_TARGETS:
        clean = dict(sorted(clean.items())[:MAX_TARGETS])
    state.start = start
    state.targets = clean
    if len(clean) != len(targets):
        state.result = None
    if not isinstance(state.get("result"), dict):
        state.result = None
    seed = state.get("random_seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**31 - 1:
        state.random_seed = DEFAULT_SEED
    state.setdefault("board_notice", "")


def _invalidate(notice=""):
    """Any change to the board retires the numbers computed from the old one."""
    st.session_state.result = None
    st.session_state.board_notice = notice


def _apply_click(cell, action, symbol):
    """Act on one board click, then restart the script.

    Rerunning rather than returning is what keeps the board whole: a return
    from inside the row loop would abandon every row still to be drawn.
    """
    targets = st.session_state.targets
    if action == "Move the start square":
        targets.pop(cell, None)
        st.session_state.start = cell
        _invalidate()
    elif action == "Erase":
        _invalidate("" if targets.pop(cell, None) else "That square was already empty.")
    elif cell == st.session_state.start:
        _invalidate("The start square cannot hold a target. "
                    "Move the start square first, or choose another square.")
    elif cell not in targets and len(targets) >= MAX_TARGETS:
        _invalidate(f"{MAX_TARGETS} targets is the maximum. Erase one first.")
    else:
        targets[cell] = symbol
        _invalidate()
    st.rerun()


# --------------------------------------------------------------------------
# board
# --------------------------------------------------------------------------
def _board_css(start, targets):
    """One short rule per square: the checker pattern, the start ring, targets."""
    rules = []
    for cell in range(64):
        rank, file = divmod(cell, 8)
        base = PALETTE["square_dark"] if (rank + file) % 2 == 0 else PALETTE["square_light"]
        if cell == start:
            fill = (f"background:{PALETTE['green']};"
                    f"box-shadow:inset 0 0 0 2px {PALETTE['green_bright']}")
        elif cell in targets:
            fill = f"background:{base};box-shadow:inset 0 0 20px rgba(85,203,178,.16)"
        else:
            fill = f"background:{base}"
        rules.append(f".st-key-square_{cell} button{{{fill}!important}}")
    return "<style>" + "".join(rules) + "</style>"


def _board(action, symbol):
    """Draw the eight ranks with a coordinate gutter, newest state first."""
    start, targets = st.session_state.start, st.session_state.targets
    st.html(_board_css(start, targets))
    if st.session_state.board_notice:
        st.warning(st.session_state.board_notice, icon="⚠")
    else:
        st.caption(f"Start {name(start)} · {len(targets)} of {MAX_TARGETS} targets "
                   f"· click to {action.lower()}")
    with st.container(key="boardgrid"):
        for rank in range(7, -1, -1):
            columns = st.columns([0.42] + [1] * 8, gap="small",
                                 vertical_alignment="center")
            columns[0].html(f'<div class="osa-coord">{rank + 1}</div>')
            for file in range(8):
                cell = rank * 8 + file
                label = targets.get(cell, "✦" if cell == start else " ")
                if columns[file + 1].button(label, key=f"square_{cell}",
                                            help=name(cell), width="stretch"):
                    _apply_click(cell, action, symbol)
        letters = st.columns([0.42] + [1] * 8, gap="small")
        for file, letter in enumerate("abcdefgh"):
            letters[file + 1].html(
                f'<div class="osa-coord osa-coord-file">{letter}</div>')


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
def _controls(revealed):
    """The right-hand panel. Runs before the board, so the board sees the result."""
    action = st.radio("Click action", ACTIONS, horizontal=True, key="board_action")
    symbol = "♟"
    if action == "Place a target":
        symbol = st.segmented_control("Symbol", SYMBOLS, default="♟",
                                      key="board_symbol") or "♟"
        st.caption("The symbol is decoration. Every target behaves identically.")

    with st.expander("Example boards from the slides", expanded=not revealed):
        for row in (list(EXAMPLES)[:2], list(EXAMPLES)[2:]):
            for label, column in zip(row, st.columns(2)):
                if column.button(label, key=f"example_{label}", width="stretch"):
                    start_name, target_names = EXAMPLES[label]
                    st.session_state.start = square(start_name)
                    st.session_state.targets = {square(n): "♟" for n in target_names}
                    _invalidate()

    with st.expander("Random board", expanded=False):
        count = st.slider("Targets", 1, MAX_TARGETS, 4, key="random_count")
        seed = st.number_input("Seed", min_value=0, max_value=2**31 - 1,
                               key="random_seed",
                               help="The same seed always rebuilds the same board.")
        place, clear = st.columns(2)
        if place.button("Place", key="random_place", width="stretch"):
            rng = random.Random(int(seed))
            cells = rng.sample([c for c in range(64)
                                if c != st.session_state.start], count)
            st.session_state.targets = {c: rng.choice(SYMBOLS) for c in cells}
            _invalidate()
        if clear.button("Clear board", key="clear_board", width="stretch"):
            st.session_state.targets = {}
            _invalidate()

    if st.button("Compute", type="primary", width="stretch", key="compute"):
        targets = tuple(sorted(st.session_state.targets))
        try:
            with st.spinner("Searching every route…"):
                st.session_state.result = {
                    piece: solve(st.session_state.start, targets, piece)
                    for piece in PIECES}
            st.session_state.board_notice = ""
        except (ValueError, RuntimeError) as error:
            st.session_state.result = None
            st.error(f"This board cannot be solved: {error}")

    result = st.session_state.result
    if result:
        left, right = st.columns(2)
        left.metric("Rook" if revealed else "A", result["rook"]["moves"])
        right.metric("Knight" if revealed else "B", result["knight"]["moves"])
        if revealed:
            st.caption(f"{result['rook']['states_examined'] + result['knight']['states_examined']:,}"
                       " states examined across the two exact searches.")
    else:
        note("Place targets, then press Compute.")

    if not revealed:
        st.text_input("Your hypothesis: what might A and B measure?", key="hypothesis")
        st.caption("Then choose one change to the board that would disprove it.")
    else:
        st.caption("Both trials start on the highlighted square. "
                   "Every placed symbol is an identical stationary target.")
    return action, symbol


# --------------------------------------------------------------------------
# replay
# --------------------------------------------------------------------------
def _replay_figure(result, step):
    """Draw the board at one point along the route: captured, remaining, trail."""
    path = result["path"]
    here = path[step]
    captured = [t for t in result["targets"] if t in set(path[:step + 1])]
    remaining = [t for t in result["targets"] if t not in set(path[:step + 1])]
    figure = go.Figure()
    for cell in range(64):
        rank, file = divmod(cell, 8)
        figure.add_shape(type="rect", x0=file, y0=rank, x1=file + 1, y1=rank + 1,
                         line_width=0,
                         fillcolor=PALETTE["square_dark"] if (rank + file) % 2 == 0
                         else PALETTE["square_light"], layer="below")
    figure.add_shape(type="rect", x0=0, y0=0, x1=8, y1=8, layer="below",
                     line=dict(color=PALETTE["line"], width=1))
    figure.add_shape(type="rect", x0=here % 8, y0=here // 8, x1=here % 8 + 1,
                     y1=here // 8 + 1, fillcolor=PALETTE["green"], layer="below",
                     line=dict(color=PALETTE["green_bright"], width=2))
    if step:
        figure.add_trace(go.Scatter(
            x=[cell % 8 + .5 for cell in path[:step + 1]],
            y=[cell // 8 + .5 for cell in path[:step + 1]],
            mode="lines+markers", showlegend=False, hoverinfo="skip",
            line=dict(color=PALETTE["green_pale"], width=2),
            marker=dict(size=6, color=PALETTE["green_pale"])))
    # A captured target is ghosted rather than erased, so the route reads as a
    # sequence of captures instead of pieces simply vanishing.
    for cell in captured:
        figure.add_annotation(x=cell % 8 + .5, y=cell // 8 + .5, text="♟",
                              showarrow=False,
                              font=dict(size=28, color="rgba(244,247,246,0.22)"))
    for cell in remaining:
        figure.add_annotation(x=cell % 8 + .5, y=cell // 8 + .5, text="♟",
                              showarrow=False, font=dict(size=30, color=PALETTE["text"]))
    figure.add_annotation(x=here % 8 + .5, y=here // 8 + .5,
                          text="♜" if result["piece"] == "rook" else "♞",
                          showarrow=False, font=dict(size=33, color="#FFFFFF"))
    axis = dict(range=[0, 8], tickvals=[i + .5 for i in range(8)], fixedrange=True,
                showgrid=False, zeroline=False, tickfont=dict(color=PALETTE["dim"], size=11))
    figure.update_layout(
        height=430, paper_bgcolor=PALETTE["ink"], plot_bgcolor=PALETTE["ink"],
        margin=dict(l=26, r=10, t=10, b=26),
        xaxis=dict(ticktext=list("abcdefgh"), constrain="domain", **axis),
        yaxis=dict(ticktext=list("12345678"), scaleanchor="x", constrain="domain", **axis))
    return figure


def _replay(seed):
    """Step through a shortest route and export the whole experiment."""
    results = st.session_state.result
    st.markdown("#### Replay a shortest route")
    choose, scrub = st.columns([1, 1.6], gap="medium")
    piece = choose.radio("Replay", list(PIECES), horizontal=True, key="replay_piece",
                         format_func=str.capitalize, label_visibility="collapsed")
    result = results[piece]
    total = result["moves"]
    # The key carries the route length, so switching piece can never leave the
    # slider holding a step number that is out of range for the new route.
    step = scrub.slider("Move", 0, total, 0, key=f"replay_step_{piece}_{total}",
                        label_visibility="collapsed") if total else 0

    st.plotly_chart(_replay_figure(result, step), width="stretch",
                    config={"displayModeBar": False})
    squares = [name(cell) for cell in result["path"]]
    st.html('<div style="font-family:ui-monospace,monospace;font-size:1rem;'
            f'line-height:2;color:{PALETTE["dim"]}"><b style="color:{PALETTE["muted"]};'
            f'font-family:inherit">Move {step} of {total}</b>&nbsp;&nbsp;'
            + " → ".join(
                f'<span style="color:{PALETTE["green_bright"]};font-weight:700">{s}</span>'
                if i == step else s for i, s in enumerate(squares))
            + "</div>")
    legal = verify(result)
    st.caption(f"Independent replay legal: **{legal}**. Exact minimum: "
               f"**{total}**. States examined: {result['states_examined']:,}.")
    if not legal:
        st.error("The replay check failed. Do not trust this route; "
                 "please report the board that produced it.")
    payload = {
        "activity": "MiniChess",
        "rules_version": "1.1.0",
        "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": name(st.session_state.start),
        "targets": {name(cell): symbol
                    for cell, symbol in sorted(st.session_state.targets.items())},
        "random_seed": int(seed),
        "results": {key: {**value,
                          "path_squares": [name(cell) for cell in value["path"]],
                          "replay_legal": verify(value)}
                    for key, value in results.items()},
    }
    st.download_button("Download this experiment and both routes",
                       json.dumps(payload, indent=2, ensure_ascii=False),
                       "minichess_experiment.json", "application/json",
                       width="stretch")


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------
def render():
    """Draw the whole activity. Safe to call on every rerun."""
    _sanitize_state()
    page_header("Activity one", "MiniChess",
                "A board, a highlighted square and two numbers. "
                "Work out what the numbers mean before the rules are revealed.")
    mode = st.radio("Round", ["1 · What do the numbers mean?",
                              "2 · Open the instruction book"],
                    horizontal=True, key="round", label_visibility="collapsed")
    revealed = mode.startswith("2")
    st.divider()

    board_column, control_column = st.columns([1.15, 1], gap="large")
    # Controls run first so a preset or random board is drawn in the same run.
    with control_column:
        action, symbol = _controls(revealed)
    with board_column:
        _board(action, symbol)

    if revealed:
        st.divider()
        rules_column, replay_column = st.columns([1, 1.3], gap="large")
        with rules_column:
            st.markdown(RULES)
        with replay_column:
            if st.session_state.result:
                _replay(st.session_state.random_seed)
            else:
                note("Press Compute to unlock the step-by-step replay.")
        listing = "Read the exact solver" if SOURCE_FILES else \
            "Read the complete code that is running"
        with st.expander(listing):
            for filename, text in source_files(*SOURCE_FILES).items():
                st.caption(filename)
                st.code(text, language="python")

    footer("Concept: Sinuhé Perea, Equilibrium. "
           "Workshop implementation: Sinuhé Perea with AI assistance.",
           '<a href="https://sites.google.com/view/sinuheperea/equilibrium?authuser=0">'
           "Original Equilibrium page</a>")
