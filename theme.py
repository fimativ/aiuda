"""Shared visual language: palette, stylesheet and page furniture.

Presentation only. No workshop logic lives here, so either activity can be
read and judged without reference to how it happens to be painted.
"""
from pathlib import Path
from string import Template
import streamlit as st

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
