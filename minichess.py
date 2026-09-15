"""MiniChess — Sinuhé Perea · OSA / MPG · 15 September 2026.

Run:     python3 -m streamlit run minichess.py
Install: python3 -m pip install 'streamlit>=1.58,<2' 'plotly>=5.17,<7'

GENERATED FILE — do not edit by hand. It is assembled from theme.py, chess_engine.py, chess_ui.py
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
import random
import streamlit as st

from collections import deque
from datetime import datetime, timezone
from functools import lru_cache
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
# chess_engine.py
# ========================================================================

FILES = "abcdefgh"
RANKS = "12345678"
VERSION = "1.1.0"
MAX_TARGETS = 8
PIECES = ("rook", "knight")


def square(name):
    """Convert algebraic notation such as 'e4' into a 0-63 board index."""
    if not isinstance(name, str) or len(name) != 2:
        raise ValueError("Use a square from a1 to h8")
    file_letter, rank_digit = name[0].lower(), name[1]
    if file_letter not in FILES or rank_digit not in RANKS:
        raise ValueError(f"{name!r} is not a square from a1 to h8")
    return (int(rank_digit) - 1) * 8 + FILES.index(file_letter)


def name(cell):
    """Convert a 0-63 board index back into algebraic notation."""
    if not isinstance(cell, int) or isinstance(cell, bool) or not 0 <= cell < 64:
        raise ValueError(f"{cell!r} is not a square index between 0 and 63")
    return FILES[cell % 8] + RANKS[cell // 8]


def on_board(cell):
    """True when cell is usable as a board index. Never raises."""
    return isinstance(cell, int) and not isinstance(cell, bool) and 0 <= cell < 64


def legal_moves(position, occupied, piece):
    """Yield every square the piece may reach in one move from position.

    occupied holds the targets still on the board. A rook stops on the first
    one it meets and may capture it; a knight ignores them entirely and
    captures only on the square where it lands.
    """
    row, col = divmod(position, 8)
    if piece == "knight":
        for d_row, d_col in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                             (1, -2), (1, 2), (2, -1), (2, 1)):
            r, c = row + d_row, col + d_col
            if 0 <= r < 8 and 0 <= c < 8:
                yield r * 8 + c
    elif piece == "rook":
        for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = row + d_row, col + d_col
            while 0 <= r < 8 and 0 <= c < 8:
                reached = r * 8 + c
                yield reached
                if reached in occupied:
                    break
                r, c = r + d_row, c + d_col
    else:
        raise ValueError("Piece must be rook or knight")


def _validate(start, targets, piece):
    """Normalise the arguments or explain exactly why they are unusable."""
    if not on_board(start):
        raise ValueError("The starting square is outside the board")
    targets = tuple(sorted(targets))
    if any(not on_board(t) for t in targets):
        raise ValueError("A target square is outside the board")
    if len(set(targets)) != len(targets):
        raise ValueError("Targets must be unique")
    if start in targets:
        raise ValueError("A target cannot sit on the starting square")
    if len(targets) > MAX_TARGETS:
        raise ValueError(f"At most {MAX_TARGETS} targets for exact interactive search")
    if piece not in PIECES:
        raise ValueError("Piece must be rook or knight")
    return start, targets, piece


@lru_cache(maxsize=512)
def _search(start, targets, piece):
    """Breadth-first search over (square, remaining targets). Cached, so the
    dictionary it returns is shared; solve() hands out a copy instead.
    """
    bits = {cell: 1 << i for i, cell in enumerate(targets)}
    initial = (start, (1 << len(targets)) - 1)
    parent = {initial: None}
    queue = deque([initial])
    examined = 0
    while queue:
        state = queue.popleft()
        examined += 1
        position, mask = state
        if mask == 0:
            path = []
            while state is not None:
                path.append(state[0])
                state = parent[state]
            path.reverse()
            return {"moves": len(path) - 1, "path": path, "states_examined": examined,
                    "piece": piece, "start": start, "targets": list(targets),
                    "engine_version": VERSION, "optimal": True}
        occupied = {t for t in targets if mask & bits[t]}
        for reached in legal_moves(position, occupied, piece):
            following = (reached, mask & ~bits.get(reached, 0))
            if following not in parent:
                parent[following] = state
                queue.append(following)
    raise RuntimeError("No capture route found")  # unreachable: both pieces reach every square


def solve(start, targets, piece):
    """Return the shortest capture route as a fresh, self-contained dictionary.

    Keys: moves, path, states_examined, piece, start, targets, engine_version,
    optimal. The caller owns the result and may edit it without disturbing the
    cache that made the search fast.
    """
    start, targets, piece = _validate(start, targets, piece)
    found = _search(start, targets, piece)
    return {**found, "path": list(found["path"]), "targets": list(found["targets"])}


def verify(result):
    """Replay the route independently and report whether every step is legal.

    This checks legality only. Optimality comes from the breadth-first order of
    the search, which a replay alone could never establish.
    """
    try:
        remaining = set(result["targets"])
        path = result["path"]
        piece = result["piece"]
        if not path or path[0] != result["start"] or result["moves"] != len(path) - 1:
            return False
        if piece not in PIECES or any(not on_board(cell) for cell in path):
            return False
        for here, there in zip(path, path[1:]):
            if there not in set(legal_moves(here, remaining, piece)):
                return False
            remaining.discard(there)
        return not remaining
    except (KeyError, TypeError):
        return False


# ========================================================================
# chess_ui.py
# ========================================================================

# The build script rewrites this to () for the generated single-file app,
# so each build shows the audience exactly the file that is running.
SOURCE_FILES = ()

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


# ========================================================================
# entry point
# ========================================================================

page_setup("MiniChess")
sidebar_identity()
render()
