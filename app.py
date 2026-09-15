"""What AI Can (Un)veil for Open Science — both workshop activities in one app.

Run: streamlit run app.py

Workshop data stay in this app's server session. Public hosting runs this
Python code on the host; it is not browser-only privacy. No AI model is
called and no answer database is created.
"""
import streamlit as st

import chess_ui
import compass_ui
from theme import PALETTE, footer, page_header, page_setup, sidebar_identity

page_setup("What AI Can (Un)veil")

ACTIVITIES = {
    "MiniChess": chess_ui.render,
    "Research Compass": compass_ui.render,
}

READING = [
    ("Mathematics and AI", [
        ("Mathematics in the age of AI — Terence Tao (2026)",
         "https://arxiv.org/abs/2608.16753"),
        ("Math and AI statement", "https://mathandai.org/"),
        ("First Proof community experiment",
         "https://1stproof.org/community-experiment.html"),
        ("Leiden Declaration on AI and Mathematics", "https://leidendeclaration.ai/"),
        ("Stochastic Parrots — Bender et al. (2021)",
         "https://doi.org/10.1145/3442188.3445922"),
    ]),
    ("Open science commitments", [
        ("Berlin Declaration", "https://openaccess.mpg.de/Berlin-Declaration"),
        ("OSA, PhDnet and PostdocNet Joint Statement",
         "https://pure.mpg.de/view/item_3694922"),
        ("Open Source Definition", "https://opensource.org/osd"),
    ]),
    ("Things you can join or use", [
        ("Zooniverse", "https://www.zooniverse.org/about"),
        ("AlternativeTo", "https://alternativeto.net/"),
        ("Sinuhé's digital garden", "https://sites.google.com/view/sinuheperea/home"),
    ]),
]


def resources():
    """Closing page: where to read further and where the ideas came from."""
    page_header("Afterwards", "The open notebook",
                "Everything referenced in the session, plus the film, in one place.")
    st.divider()
    for column, (heading, links) in zip(st.columns(len(READING), gap="large"), READING):
        with column:
            st.markdown(f"##### {heading}")
            st.html('<div style="line-height:2.1;font-size:.92rem">'
                    + "<br>".join(f'<a href="{url}">{label}</a>'
                                  for label, url in links) + "</div>")
    st.divider()
    film, blurb = st.columns([1.35, 1], gap="large")
    with film:
        st.video("https://www.youtube.com/watch?v=80dR30uGdyQ")
    with blurb:
        st.markdown("##### ShoeTool · Free Software Foundation")
        st.write("Two minutes on what it means to be allowed to repair the "
                 "tools you depend on.")
        st.caption("© 2019 FSF, CC BY-SA 4.0. Producer/director Brad Burkhart; "
                   "animator Zygis Luksas; story Douglas J. Eboch. 2:05.")
        # A venue network that blocks the embed should not strand the session.
        st.html('<div style="font-size:.82rem">If the player stays blank, open '
                '<a href="https://www.youtube.com/watch?v=80dR30uGdyQ">the film '
                "directly</a>. It needs an internet connection and is served by "
                "YouTube.</div>")
    footer("<b>TRUE</b> · Transparent · Reproducible · Usable by others · Extensible",
           "Concept and direction: Sinuhé Perea. Implementation developed with "
           "AI assistance. Original workshop code under the MIT licence.")


st.sidebar.html('<div class="osa-kicker">Session</div>')
activity = st.sidebar.radio("Session", list(ACTIVITIES) + ["Resources"],
                            label_visibility="collapsed")
sidebar_identity()

ACTIVITIES.get(activity, resources)()
