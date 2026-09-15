"""What AI Can (Un)veil for Open Science — Sinuhé Perea · OSA / MPG · 15 Sep 2026.

Two activities, one app, no AI model and no database.

  Board    place targets, press Compute, read two numbers.
  Compass  twelve questions; each answer moves you on a hidden map.

Run: streamlit run app.py
"""
import math
from collections import deque
from functools import lru_cache

import plotly.graph_objects as go
import streamlit as st

INK = "#000000"
GREEN = "#007367"
BRIGHT = "#55CBB2"
PALE = "#9EF2D6"
TEXT = "#F4F7F6"
MUTED = "#8FA39D"
DIM = "#5F736E"
LINE = "#1E3430"
DARK_SQ = "#162A25"
LIGHT_SQ = "#3C564E"

st.set_page_config(page_title="AI × Open Science", page_icon="◐", layout="centered")

st.html(f"""<style>
/* the Streamlit header is 60px tall and sits over the page, so the tab bar
   needs to start below it */
html{{font-size:17px}}
.block-container{{max-width:640px;padding-top:4.75rem;padding-bottom:3rem}}
header[data-testid=stHeader]{{background:{INK}}}
h1,h2,h3{{font-weight:500!important;letter-spacing:-.01em}}
.stButton button{{border-radius:8px;font-weight:450}}
[data-testid=stTabs] [role=tab] p{{font-size:1.08rem!important}}

/* Reset and Compute stay side by side on a phone */
.st-key-actions [data-testid=stHorizontalBlock]{{flex-wrap:nowrap!important}}
.st-key-actions [data-testid=stColumn]{{min-width:0!important}}

/* board: always eight across, always square, even on a phone */
[class*="st-key-sq_"] button{{aspect-ratio:1;height:auto;min-height:0;width:100%;
  padding:0;border-radius:2px;border:1px solid {INK};color:{TEXT}!important}}
[class*="st-key-sq_"] button p{{font-size:clamp(21px,5.6vw,34px)!important;line-height:1!important}}
[class*="st-key-sq_"] button:hover{{filter:brightness(1.4);border-color:{BRIGHT}!important}}
.st-key-board{{gap:0!important}}
.st-key-board [data-testid=stElementContainer]{{margin-bottom:0}}
.st-key-board [data-testid=stHorizontalBlock]{{gap:0!important;flex-wrap:nowrap!important}}
.st-key-board [data-testid=stColumn]{{min-width:0!important}}

/* answers: full-width, left-aligned, readable when they wrap */
[class*="st-key-opt_"] button{{padding:.75rem 1rem;font-size:1.02rem;border-left-width:3px;
  border-left-color:{GREEN}!important;text-align:left}}
[class*="st-key-opt_"] button > div{{width:100%;justify-content:flex-start;text-align:left}}

.big{{display:flex;gap:1.4rem;margin:.3rem 0 .2rem}}
.big > div{{flex:1;border:1px solid {LINE};border-radius:10px;padding:.5rem 0 .7rem;
  text-align:center;background:#080F0D}}
.big b{{display:block;font-size:.8rem;letter-spacing:.2em;color:{MUTED};font-weight:600}}
.big span{{display:block;font-size:3.9rem;line-height:1.1;color:{BRIGHT};font-weight:300;
  font-variant-numeric:tabular-nums}}
.dots{{display:flex;gap:4px;margin:.1rem 0 1rem}}
.dots i{{height:3px;flex:1;border-radius:2px;background:{LINE}}}
.dots i.on{{background:{BRIGHT}}}
.foot{{color:{DIM};font-size:.8rem;border-top:1px solid {LINE};padding-top:.7rem;
  margin-top:2rem;line-height:1.6}}
</style>""")


START = 0
MAX_TARGETS = 8


def moves_from(cell, blocked, piece):
    """Every square reachable in one legal move. A rook stops on the first
    target it meets and may capture it; a knight jumps over everything."""
    row, col = divmod(cell, 8)
    if piece == "knight":
        for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)):
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                yield r * 8 + c
    else:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                reached = r * 8 + c
                yield reached
                if reached in blocked:
                    break
                r, c = r + dr, c + dc


@lru_cache(maxsize=512)
def fewest_moves(start, targets, piece):
    """Exact minimum number of moves to capture every target.

    Breadth-first search over (square, set of targets still standing). States
    are visited in nondecreasing move count and every move costs one, so the
    first state with nothing left standing is a shortest solution.
    """
    bits = {cell: 1 << i for i, cell in enumerate(targets)}
    full = (1 << len(targets)) - 1
    seen = {(start, full)}
    queue = deque([(start, full, 0)])
    while queue:
        cell, left, depth = queue.popleft()
        if not left:
            return depth
        standing = {t for t in targets if left & bits[t]}
        for reached in moves_from(cell, standing, piece):
            nxt = (reached, left & ~bits.get(reached, 0))
            if nxt not in seen:
                seen.add(nxt)
                queue.append((*nxt, depth + 1))
    raise RuntimeError("unreachable: both pieces can reach every square")


QUESTIONS = [
    ("An AI model trains on thousands of copyrighted, paywalled papers to generate a new cure.", [
        ("Copyright shouldn't block progress. Release the cure and the model for free.", 2, 2),
        ("The model's creators should own the cure and patent it to fund future research.", -2, 2),
        ("This is theft. AI shouldn't bypass the original human authors' rights.", -1, -2),
        ("We need open-access papers so humans can find this without black-box algorithms.", 2, -1)]),
    ("What is the role of AI in writing scientific papers?", [
        ("A dystopian nightmare. The act of writing is the act of thinking.", 0, -2),
        ("A glorified thesaurus. Fine for grammar, but the hypothesis must be yours.", 0, -1),
        ("Keep it closed: the best proprietary drafting tool wins the best grants.", -2, 1),
        ("The future. AI should write, review and publish to a global open ledger.", 2, 2)]),
    ("An AI finds a room-temperature superconductor, but it is a complete black box.", [
        ("If it works, I don't care how. Patent it and sell the technology.", -2, 2),
        ("Unacceptable. Science requires interpretable, human-readable mechanisms.", 1, -2),
        ("Fine, but only if the weights are open-sourced for public auditing.", 2, 1),
        ("Useful, but human-led experiments must reverse-engineer its logic.", 0, -1)]),
    ("How should we handle the replicability crisis?", [
        ("Radical transparency: all raw data and code public, for human review.", 2, -1),
        ("An open-source AI agent network that replicates every published paper.", 2, 2),
        ("Proprietary AI that privately scores researchers before funding them.", -2, 1),
        ("AI makes it worse by hallucinating plausible datasets. Ban it.", 0, -2)]),
    ("What happens to citizen science in the next decade?", [
        ("AI replaces it. Autonomous sensors are more accurate than hobbyists.", -1, 2),
        ("AI empowers it. Everyone gets a research assistant on their phone.", 2, 2),
        ("It stays a human community effort. AI alienates people from nature.", 2, -2),
        ("Science is for credentialed experts. Amateurs with AI spread misinformation.", -2, 0)]),
    ("Who should peer-review the science of tomorrow?", [
        ("Nobody. Publish to open preprint servers and let the crowd filter it.", 2, -1),
        ("AI. Faster, less biased and more scalable than tired academics.", 0, 2),
        ("Double-blind human review is the gold standard. Protect it.", -1, -2),
        ("Elite institutions, using closed algorithms for quality control.", -2, 1)]),
    ("How should scientific computing power be distributed?", [
        ("Nationalise it. Equal open access to supercomputers for everyone.", 2, 1),
        ("Let private companies monopolise it; they drive the innovation.", -2, 2),
        ("Crowdfund decentralised networks to train open scientific models.", 2, 2),
        ("Divert the money back to lab equipment and fieldwork.", 0, -2)]),
    ("Your AI model predicts protein folding beautifully. What do you do with it?", [
        ("Keep the weights secret, sell an expensive API, build a company.", -2, 2),
        ("Release code, weights and training data to accelerate global medicine.", 2, 2),
        ("Open the code, but verify everything manually. I don't fully trust it.", 1, -1),
        ("Hide the method entirely and monopolise the discoveries.", -2, -1)]),
    ("What becomes of the hypothesis in the age of AI?", [
        ("AI needs none. It finds patterns humans cannot even fathom.", 0, 2),
        ("It is a human creative spark. AI is a calculator that tests it.", 0, -2),
        ("Crowdsource human hypotheses openly and use AI to test them.", 2, 1),
        ("Keep your best ones secret until you have the compute to prove them.", -2, 0)]),
    ("How should scientists communicate with the public?", [
        ("AI avatars making physics videos degrade the dignity of the profession.", 0, -2),
        ("Scientists write their own summaries, keeping a human connection.", 2, -1),
        ("Open AI translating papers into fifty languages instantly, for everyone.", 2, 2),
        ("Paywall the real science; let AI generate the free simplified version.", -2, 1)]),
    ("Who do you ultimately trust for scientific truth?", [
        ("Thousands of researchers transparently debating the open data.", 2, -2),
        ("An AI oracle, with no ego, politics or funding bias.", 0, 2),
        ("Only models whose entire training dataset is public.", 2, 1),
        ("Elite legacy institutions and their proprietary algorithms.", -2, 1)]),
    ("Your fifty-year vision for science?", [
        ("A connected hive-mind of human hobbyists and open AI agents.", 2, 2),
        ("One closed mega-corporation licensing cures to the highest bidder.", -2, 2),
        ("A return to small-scale human science, free of Big Tech.", 2, -2),
        ("Isolated elite silos using secret AI to compete for prestige.", -2, 1)]),
]

CORE_RADIUS = 3
HERE_FILL = "#0E4F45"
AWAY_FILL = "#111F1B"

SECTORS = [
    (0, "BERNERS-LEE", "The Data Liberator",
     "Information wants to be free. AI is useful, but the real revolution is open data."),
    (45, "VON NEUMANN", "The Cybernetic Architect",
     "A decentralised hive-mind where open AI agents share data and solve the universe."),
    (90, "TURING", "The Algorithmic Enigma",
     "Machine intelligence will remake science. The politics of publishing interest you less."),
    (135, "EDISON", "The Proprietary Automator",
     "Science is an industrial engine. Powerful models stay closed, and generate patents."),
    (180, "GALILEO", "The Protective Pioneer",
     "The world is not ready for your raw data. Methods stay guarded until priority is secure."),
    (225, "NEWTON", "The Lone Alchemist",
     "Science is the solitary pursuit of singular genius. Automation and crowds can wait."),
    (270, "DARWIN", "The Methodical Observer",
     "Slow, meticulous human observation. Synthetic data is antithetical to understanding."),
    (315, "SAGAN", "The Cosmic Democratizer",
     "Science belongs to everyone, driven by wonder. Automation strips the poetry out."),
]
CORE = ("CURIE", "The Pragmatic Empiricist",
        "Balanced and grounded. Open discovery, rigorous human validation, AI as a tool.")


def position(picks):
    """Sum the chosen shifts. Start at the origin."""
    x = sum(QUESTIONS[i][1][p][1] for i, p in enumerate(picks))
    y = sum(QUESTIONS[i][1][p][2] for i, p in enumerate(picks))
    return x, y


def archetype(x, y):
    """Which of the nine regions the point falls in: the core, or one sector."""
    if math.hypot(x, y) < CORE_RADIUS:
        return CORE
    angle = math.degrees(math.atan2(y, x)) % 360
    return SECTORS[int(((angle + 22.5) % 360) // 45)][1:]


def trail(picks):
    """Every position visited, from the origin onwards."""
    return [position(picks[:k]) for k in range(len(picks) + 1)]


def board_tab():
    st.session_state.setdefault("targets", set())
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("full", False)
    targets = st.session_state.targets

    rules = []
    for cell in range(64):
        row, col = divmod(cell, 8)
        base = DARK_SQ if (row + col) % 2 == 0 else LIGHT_SQ
        if cell == START:
            rules.append(f".st-key-sq_{cell} button{{background:{GREEN}!important;"
                         f"box-shadow:inset 0 0 0 2px {BRIGHT}}}")
        else:
            rules.append(f".st-key-sq_{cell} button{{background:{base}!important}}")
    st.html("<style>" + "".join(rules) + "</style>")

    with st.container(key="board"):
        for row in range(7, -1, -1):
            columns = st.columns(8, gap="small")
            for col in range(8):
                cell = row * 8 + col
                label = "✦" if cell == START else ("♟" if cell in targets else " ")
                if columns[col].button(label, key=f"sq_{cell}", width="stretch"):
                    st.session_state.full = False
                    if cell == START:
                        pass
                    elif cell in targets:
                        targets.discard(cell)
                    elif len(targets) >= MAX_TARGETS:
                        st.session_state.full = True
                    else:
                        targets.add(cell)
                    if not st.session_state.full:
                        st.session_state.result = None
                    st.rerun()

    count = f"{len(targets)} / {MAX_TARGETS}"
    st.html(f'<div style="color:{"#E0B25C" if st.session_state.full else DIM};'
            f'font-size:.78rem;margin:.6rem 0 .2rem">{count}</div>')

    with st.container(key="actions"):
        reset, compute = st.columns(2)
        if reset.button("Reset", width="stretch", key="reset"):
            st.session_state.targets = set()
            st.session_state.result = None
            st.session_state.full = False
            st.rerun()
        if compute.button("Compute", type="primary", width="stretch", key="compute"):
            frozen = tuple(sorted(targets))
            st.session_state.result = (fewest_moves(START, frozen, "rook"),
                                       fewest_moves(START, frozen, "knight"))

    result = st.session_state.result
    a, b = ("—", "—") if result is None else result
    st.html(f'<div class="big"><div><b>A</b><span>{a}</span></div>'
            f'<div><b>B</b><span>{b}</span></div></div>')


def wedge(centre_degrees, inner, outer):
    """A 45° sector as a closed polygon, ready to fill."""
    start, end = math.radians(centre_degrees - 22.5), math.radians(centre_degrees + 22.5)
    steps = [start + (end - start) * i / 16 for i in range(17)]
    points = [(inner * math.cos(t), inner * math.sin(t)) for t in steps]
    points += [(outer * math.cos(t), outer * math.sin(t)) for t in reversed(steps)]
    points.append(points[0])
    return [p[0] for p in points], [p[1] for p in points]


def compass_figure(path, reveal):
    """The map. Regions are drawn only once every question has been answered.

    `path` is every position visited, oldest first; the last one is where the
    participant now stands.
    """
    x, y = path[-1]
    here = archetype(x, y)[0] if reveal else None
    radius = math.hypot(x, y)
    view = max(14.0, 1.25 * radius) if reveal else max(9.0, 1.35 * radius)
    rim = view * 0.93
    figure = go.Figure()

    if reveal:
        for centre, name, title, _ in SECTORS:
            mine = name == here
            wx, wy = wedge(centre, CORE_RADIUS, rim)
            figure.add_trace(go.Scatter(
                x=wx, y=wy, fill="toself", mode="lines", hoverinfo="skip",
                fillcolor=HERE_FILL if mine else AWAY_FILL,
                line=dict(color=BRIGHT if mine else "#26403A", width=2 if mine else 1),
                showlegend=False))
            if mine:
                continue
            label = math.radians(centre)
            figure.add_annotation(
                x=rim * .72 * math.cos(label), y=rim * .72 * math.sin(label),
                text=name.replace(" ", "<br>").replace("-", "<br>"), showarrow=False,
                font=dict(size=13, color="#8FA7A0"))
        core_mine = here == CORE[0]
        figure.add_shape(type="circle", x0=-CORE_RADIUS, y0=-CORE_RADIUS,
                         x1=CORE_RADIUS, y1=CORE_RADIUS, layer="below",
                         fillcolor=HERE_FILL if core_mine else AWAY_FILL,
                         line=dict(color=BRIGHT if core_mine else "#26403A",
                                   width=2 if core_mine else 1))
        if not core_mine:
            figure.add_annotation(
                x=0, y=0, text=CORE[0], showarrow=False, borderpad=3,
                bgcolor=AWAY_FILL, bordercolor="#26403A",
                font=dict(size=12, color="#8FA7A0"))
    else:
        for ring in [CORE_RADIUS, 10, 20, 30]:
            if ring <= rim:
                figure.add_shape(type="circle", x0=-ring, y0=-ring, x1=ring,
                                 y1=ring, layer="below",
                                 line=dict(color="#1B342E", width=1))
        for axis in (dict(x0=-view, x1=view, y0=0, y1=0),
                     dict(x0=0, x1=0, y0=-view, y1=view)):
            figure.add_shape(type="line", layer="below", **axis,
                             line=dict(color="#16302A", width=1))

    if len(path) > 1:
        figure.add_trace(go.Scatter(
            x=[p[0] for p in path], y=[p[1] for p in path], mode="lines",
            line=dict(color=PALE, width=2), hoverinfo="skip", showlegend=False))
    figure.add_trace(go.Scatter(
        x=[x], y=[y], mode="markers", showlegend=False,
        marker=dict(size=17, color="#FFFFFF", line=dict(color=INK, width=4)),
        hovertemplate="Open science %{x}<br>AI %{y}<extra></extra>"))

    axis = dict(range=[-view, view], fixedrange=True, showgrid=False,
                zeroline=False, showticklabels=False, constrain="domain")
    figure.update_layout(
        height=420 if reveal else 330, paper_bgcolor=INK, plot_bgcolor=INK,
        margin=dict(l=4, r=4, t=4, b=4), dragmode=False,
        xaxis=dict(**axis), yaxis=dict(scaleanchor="x", **axis))
    return figure


def compass_tab():
    st.session_state.setdefault("picks", [])
    picks = st.session_state.picks
    done = len(picks) == len(QUESTIONS)

    if done:
        x, y = position(picks)
        name, title, description = archetype(x, y)
        st.markdown(f"### {name}")
        st.markdown(f"**{title}**")
        st.write(description)
    else:
        st.html('<div class="dots">'
                + "".join(f'<i class="{"on" if i < len(picks) else ""}"></i>'
                          for i in range(len(QUESTIONS))) + "</div>")
        prompt, options = QUESTIONS[len(picks)]
        st.markdown(f"**{prompt}**")
        for index, (text, _, _) in enumerate(options):
            if st.button(text, key=f"opt_{len(picks)}_{index}", width="stretch"):
                picks.append(index)
                st.rerun()
        if picks and st.button("← Back", key="back"):
            picks.pop()
            st.rerun()

    st.plotly_chart(compass_figure(trail(picks), reveal=done), width="stretch",
                    config={"displayModeBar": False, "staticPlot": True},
                    key="compass_map")

    if done and st.button("Start again", width="stretch", key="again"):
        st.session_state.picks = []
        st.rerun()


board, compass = st.tabs(["Board", "Compass"])
with board:
    board_tab()
with compass:
    compass_tab()

st.html('<div class="foot">Sinuhé Perea · OSA / MPG Open Science · 15 September 2026<br>'
        "The compass is a conversation starter, not a measurement of anybody. "
        "No AI model is called and no answers are stored.</div>")
