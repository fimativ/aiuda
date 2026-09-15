# AI × Open Science

Sinuhé Perea · OSA / MPG Open Science community · 15 September 2026.

One Streamlit app, two tabs, one file. No AI model is called, nothing is stored.

```sh
python3 -m pip install -r requirements.txt
streamlit run app.py
```

Or `./run_local.sh`. Keep `.streamlit/config.toml` beside `app.py` for the black
and green theme.

## Board

Tap squares to place up to eight pieces. The marked corner is where both trials
start. **Compute** returns two numbers:

- **A** — fewest rook moves to capture every piece.
- **B** — the same for a knight.

Both are exact, found by breadth-first search over (square, pieces still
standing). The first completed state is a shortest one, because the search
visits states in nondecreasing move count and every move costs one.

Boards from the slides, all reproduced by the solver:

| Pieces from the marked corner | A | B |
| --- | --- | --- |
| 2 in a row | 2 | 5 |
| 3 in a row | 3 | 7 |
| 4 in a row | 4 | 9 |
| 3 on the diagonal | 6 | 6 |

## Compass

Twelve questions. Each answer shifts you by (x, y): **x** is open science,
**y** is AI integration, each option worth between −2 and +2 on each axis.
You start at the origin and watch the point drift. The map stays hidden until
the twelfth answer.

The map is radial, not a grid. A small circle of radius 3 around the origin is
the core; beyond it, eight 45° sectors:

| Region | Archetype |
| --- | --- |
| radius < 3 | Curie · the pragmatic empiricist |
| east | Berners-Lee · the data liberator |
| north-east | von Neumann · the cybernetic architect |
| north | Turing · the algorithmic enigma |
| north-west | Edison · the proprietary automator |
| west | Galileo · the protective pioneer |
| south-west | Newton · the lone alchemist |
| south | Darwin · the methodical observer |
| south-east | Sagan · the cosmic democratizer |

The map is drawn to fit wherever you land, so the result fills the frame
whether you finish near the middle or out at radius 30. Only the angle decides
the region, so scaling the outer edge changes nothing about the answer. Your
own region is left unlabelled on the map because it is already the heading
above it.

The names are mnemonics for regions of a diagram, not claims about those
scientists and not a measurement of the participant. All twelve questions and
every (x, y) are in `app.py`, in one list near the top.

### Tuning the core

`CORE_RADIUS = 3` decides how much of the map belongs to Curie. Answering at
random lands there about 9% of the time; at 4 it would be 15%, at 8 more than
half, because opposite answers cancel out. It is the one number worth
reconsidering if the balance feels wrong.

## Verify

```sh
python3 -m unittest -v test_app.py
```

Twenty-one checks: the four boards above, every single-target distance against
independent geometry, rook blocking, the eight-piece cap, the shape of the
instrument, each sector claiming its own angle, all nine regions being
reachable, the map staying hidden until the end, exactly one region being
highlighted, the point never falling outside the drawn map, and the live flows
for placing, computing, resetting, answering, going back and starting again.

Tested with Python 3.10, Streamlit 1.58 and Plotly 5.17.

## Files

| File | |
| --- | --- |
| `app.py` | the whole app: solver, questions, map, interface |
| `test_app.py` | the checks above |
| `requirements.txt`, `.streamlit/config.toml`, `run_local.sh` | to run it |

Concept and direction: Sinuhé Perea. Compass questions and archetypes drafted
with Gemini, implemented here. Built with AI assistance.
