"""Checks for both workshop activities: the exact solver, the instrument,
the live Streamlit flows, and the freshness of the generated single-file apps.

    python3 -m unittest -v test_workshop.py
"""
import random
import unittest
from collections import deque

import build_standalone
from chess_engine import MAX_TARGETS, legal_moves, name, solve, square, verify
from chess_ui import EXAMPLES
from compass_engine import KEYS, QUESTIONS, sanitize, score


def knight_distance(start, target):
    """An independent breadth-first distance, written without the solver."""
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        cell, depth = queue.popleft()
        if cell == target:
            return depth
        for other in range(64):
            if sorted((abs(cell // 8 - other // 8), abs(cell % 8 - other % 8))) == [1, 2] \
                    and other not in seen:
                seen.add(other)
                queue.append((other, depth + 1))


def load(filename="app.py"):
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(filename, default_timeout=60).run()


def press(app, *, key=None, label=None):
    """Click the first matching button and rerun, asserting no exception."""
    button = next(b for b in app.button
                  if (key is None or b.key == key) and (label is None or b.label == label))
    button.click().run()
    assert not app.exception, app.exception
    return app


def squares_drawn(app):
    return {int(b.key.split("_")[1]) for b in app.button
            if b.key and b.key.startswith("square_")}


class SolverTests(unittest.TestCase):
    def test_workshop_counterexamples(self):
        for names, expected in [(("b1", "c1", "d1"), (3, 7)), (("b2", "c3", "d4"), (6, 6))]:
            for piece, moves in zip(("rook", "knight"), expected):
                result = solve(0, tuple(map(square, names)), piece)
                self.assertEqual(result["moves"], moves)
                self.assertTrue(verify(result))

    def test_every_preset_matches_the_slides(self):
        """The four one-click boards must reproduce the pairs on the slides."""
        expected = {"2 in a row": (2, 5), "3 in a row": (3, 7),
                    "4 in a row": (4, 9), "3 diagonal": (6, 6)}
        for label, (start, targets) in EXAMPLES.items():
            pair = tuple(solve(square(start), tuple(map(square, targets)), piece)["moves"]
                         for piece in ("rook", "knight"))
            self.assertEqual(pair, expected[label], label)

    def test_all_single_target_distances(self):
        for target in range(1, 64):
            self.assertEqual(solve(0, (target,), "rook")["moves"],
                             1 if target // 8 == 0 or target % 8 == 0 else 2)
            self.assertEqual(solve(0, (target,), "knight")["moves"],
                             knight_distance(0, target))

    def test_blocking_and_capture(self):
        self.assertIn(1, legal_moves(0, {1, 3}, "rook"))
        self.assertNotIn(2, legal_moves(0, {1, 3}, "rook"))
        self.assertIn(17, legal_moves(0, {1, 8}, "knight"))

    def test_empty_invalid_and_corrupt_path(self):
        self.assertEqual(solve(0, (), "rook")["moves"], 0)
        for targets in [(0,), (1, 1), tuple(range(1, 10)), (64,), (-1,)]:
            with self.assertRaises(ValueError):
                solve(0, targets, "rook")
        for start in (-1, 64, "a1", True):
            with self.assertRaises(ValueError):
                solve(start, (1,), "rook")
        with self.assertRaises(ValueError):
            solve(0, (1,), "bishop")
        corrupt = solve(0, (1,), "rook")
        corrupt["path"] = [0, 9]
        self.assertFalse(verify(corrupt))
        self.assertFalse(verify({"nonsense": True}))

    def test_results_are_not_shared_between_callers(self):
        """A cached result must never be handed out as a shared mutable object."""
        first = solve(0, (1, 2, 3), "rook")
        second = solve(0, (3, 2, 1), "rook")
        self.assertIsNot(first, second)
        self.assertIsNot(first["path"], second["path"])
        first["moves"] = 999
        first["path"].append(63)
        self.assertEqual(solve(0, (1, 2, 3), "rook")["moves"], 3)
        self.assertEqual(len(solve(0, (1, 2, 3), "rook")["path"]), 4)

    def test_seeded_eight_target_routes(self):
        for seed in range(5):
            targets = tuple(random.Random(seed).sample(range(1, 64), MAX_TARGETS))
            for piece in ("rook", "knight"):
                result = solve(0, targets, piece)
                self.assertTrue(verify(result))
                self.assertGreaterEqual(result["moves"], MAX_TARGETS)

    def test_square_and_name_round_trip(self):
        for cell in range(64):
            self.assertEqual(square(name(cell)), cell)
        self.assertEqual(square("E4"), square("e4"))
        for bad in ("i1", "a9", "a", "", "a10", 4):
            with self.assertRaises(ValueError):
                square(bad)


class InstrumentTests(unittest.TestCase):
    def test_extrema_and_reverse(self):
        for desired in (0, 4):
            answers = {key: 4 - desired if reverse else desired
                       for key, _, reverse, _ in QUESTIONS}
            result = score(answers)
            self.assertEqual(result["open"], 25 * desired)
            self.assertEqual(result["ai"], 25 * desired)
            self.assertTrue(result["complete"])

    def test_skips_are_not_zero(self):
        answers = {key: 2 for key in KEYS}
        for key in ("O1", "O2", "A1", "A2"):
            answers[key] = None
        result = score(answers)
        self.assertEqual(result["open"], 50)
        self.assertEqual(result["ai"], 50)
        self.assertFalse(result["complete"])
        answers["O3"] = None
        self.assertIsNone(score(answers)["open"])
        self.assertNotIn("archetype", score(answers))

    def test_invalid_answers_are_rejected(self):
        for value in (-1, 5, True, "3", 2.0):
            with self.assertRaises(ValueError):
                score({"O1": value})
        with self.assertRaises(ValueError):
            score(["O1"])

    def test_sanitize_survives_a_stale_session(self):
        self.assertEqual(sanitize({"O1": 2, "ZZ": 9, "A1": "x", "A2": None}),
                         {"O1": 2, "A2": None})
        for junk in (None, "answers", 7, []):
            self.assertEqual(sanitize(junk), {})

    def test_every_band_combination_names_an_archetype(self):
        for low, high in ((0, 4), (2, 2), (4, 0)):
            answers = {key: (low if axis == "open" else high) for key, axis, _, _ in QUESTIONS}
            answers = {key: (4 - value if reverse else value)
                       for (key, _, reverse, _), value in zip(QUESTIONS, answers.values())}
            self.assertIn("archetype", score(answers))


class ChessAppTests(unittest.TestCase):
    def test_example_compute_and_reveal(self):
        app = load()
        press(app, key="example_3 in a row")
        press(app, key="compute")
        self.assertEqual([m.value for m in app.metric], ["3", "7"])
        self.assertEqual([m.label for m in app.metric], ["A", "B"])
        next(r for r in app.radio if r.label == "Round") \
            .set_value("2 · Open the instruction book").run()
        self.assertFalse(app.exception)
        self.assertEqual([m.label for m in app.metric], ["Rook", "Knight"])
        press(app, key="clear_board")
        press(app, key="compute")
        self.assertEqual([m.value for m in app.metric], ["0", "0"])

    def test_rejected_click_keeps_the_whole_board(self):
        """A refused click must warn without deleting the rest of the page."""
        app = load()
        self.assertEqual(len(squares_drawn(app)), 64)
        start = app.session_state["start"]
        press(app, key=f"square_{start}")
        self.assertEqual(len(squares_drawn(app)), 64)
        self.assertTrue(app.warning)
        self.assertTrue(any("Equilibrium" in element.body for element in app.get("html")))

    def test_target_cap_warns_without_losing_squares(self):
        app = load()
        app.get("slider")[0].set_value(MAX_TARGETS).run()
        press(app, key="random_place")
        self.assertEqual(len(app.session_state["targets"]), MAX_TARGETS)
        free = next(c for c in range(64) if c not in app.session_state["targets"]
                    and c != app.session_state["start"])
        press(app, key=f"square_{free}")
        self.assertEqual(len(squares_drawn(app)), 64)
        self.assertIn("maximum", app.warning[0].value)
        self.assertEqual(len(app.session_state["targets"]), MAX_TARGETS)

    def test_editing_the_board_retires_the_old_numbers(self):
        app = load()
        press(app, key="example_3 in a row")
        press(app, key="compute")
        self.assertIsNotNone(app.session_state["result"])
        free = next(c for c in range(64) if c not in app.session_state["targets"]
                    and c != app.session_state["start"])
        press(app, key=f"square_{free}")
        self.assertIsNone(app.session_state["result"])
        self.assertEqual(app.metric, [])

    def test_moving_the_start_square_clears_any_target_on_it(self):
        app = load()
        press(app, key="example_3 in a row")
        occupied = min(app.session_state["targets"])
        next(r for r in app.radio if r.label == "Click action") \
            .set_value("Move the start square").run()
        press(app, key=f"square_{occupied}")
        self.assertEqual(app.session_state["start"], occupied)
        self.assertNotIn(occupied, app.session_state["targets"])
        self.assertFalse(app.exception)

    def test_corrupt_session_state_is_repaired(self):
        app = load()
        app.session_state["start"] = 999
        app.session_state["targets"] = {"nonsense": "♟", 5: "X", 6: "♟"}
        app.session_state["random_seed"] = -4
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["start"], square("e4"))
        self.assertEqual(app.session_state["targets"], {6: "♟"})
        self.assertEqual(len(squares_drawn(app)), 64)

    def test_replay_survives_switching_piece(self):
        app = load()
        press(app, key="example_3 diagonal")
        press(app, key="compute")
        next(r for r in app.radio if r.label == "Round") \
            .set_value("2 · Open the instruction book").run()
        step = next(s for s in app.slider if s.label == "Move")
        step.set_value(step.max).run()
        next(r for r in app.radio if r.label == "Replay").set_value("knight").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("legal: **True**" in c.value for c in app.caption))


class CompassAppTests(unittest.TestCase):
    def open_compass(self):
        app = load()
        next(r for r in app.radio if r.label == "Session").set_value("Research Compass").run()
        return app

    def answer_all(self, app, value=3):
        for _ in range(12):
            press(app, key=f"answer_{KEYS[app.session_state['question']]}_{value}")
        return app

    def test_complete_then_restart(self):
        app = self.answer_all(self.open_compass())
        self.assertTrue(app.session_state["show_result"])
        self.assertEqual(len(app.session_state["answers"]), 12)
        self.assertTrue(any("Leonardo" in s.value or "Commons" in s.value
                            for s in app.subheader))
        press(app, key="restart")
        self.assertEqual(app.session_state["answers"], {})
        self.assertEqual(app.session_state["question"], 0)
        self.assertFalse(app.session_state["show_result"])

    def test_back_button(self):
        app = self.open_compass()
        press(app, key="answer_O1_3")
        self.assertEqual(app.session_state["question"], 1)
        press(app, key="nav_back")
        self.assertEqual(app.session_state["question"], 0)

    def test_review_offers_a_route_back_to_the_result(self):
        app = self.answer_all(self.open_compass())
        press(app, key="review")
        self.assertFalse(app.session_state["show_result"])
        press(app, key="nav_result")
        self.assertTrue(app.session_state["show_result"])
        self.assertEqual(len(app.session_state["answers"]), 12)

    def test_advancing_never_erases_a_saved_answer(self):
        """During review, moving on must keep the answer already recorded."""
        app = self.answer_all(self.open_compass())
        press(app, key="review")
        forward = next(b for b in app.button if b.key == "nav_next")
        self.assertEqual(forward.label, "Next")
        press(app, key="nav_next")
        self.assertEqual(app.session_state["answers"]["O1"], 3)
        press(app, key="nav_back")
        press(app, key="nav_clear")
        self.assertIsNone(app.session_state["answers"]["O1"])
        self.assertEqual(next(b for b in app.button if b.key == "nav_next").label, "Skip")

    def test_skipping_everything_is_handled(self):
        app = self.open_compass()
        for _ in range(12):
            press(app, key="nav_next")
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["show_result"])
        self.assertTrue(app.info)
        self.assertEqual(app.button[0].key, "review")

    def test_out_of_range_question_is_clamped(self):
        app = self.open_compass()
        app.session_state["question"] = 99
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["question"], 11)
        app.session_state["question"] = -5
        app.run()
        self.assertEqual(app.session_state["question"], 0)

    def test_stale_answers_do_not_crash_the_page(self):
        app = self.open_compass()
        app.session_state["answers"] = {"O1": 9, "GONE": 2, "A1": 3}
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["answers"], {"A1": 3})


class StandaloneTests(unittest.TestCase):
    def test_generated_files_are_current(self):
        """The single-file apps must match a fresh build of the modules."""
        for filename in build_standalone.BUILDS:
            with open(filename, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), build_standalone.build(filename),
                                 f"{filename} is stale; run build_standalone.py")

    def test_each_standalone_runs(self):
        for filename in build_standalone.BUILDS:
            app = load(filename)
            self.assertFalse(app.exception, f"{filename}: {app.exception}")
            self.assertTrue(app.button, f"{filename} rendered no controls")

    def test_standalone_shows_its_own_complete_source(self):
        """The single-file build must offer the file that is actually running."""
        for filename in build_standalone.BUILDS:
            app = load(filename)
            if filename == "minichess.py":   # the solver is shown in round two
                next(r for r in app.radio if r.label == "Round") \
                    .set_value("2 · Open the instruction book").run()
            listed = "\n".join(block.value for block in app.get("code"))
            self.assertIn("page_setup(", listed, filename)
            self.assertIn("def render()", listed, filename)
            self.assertNotIn("import chess_engine", listed)
            self.assertNotIn("import compass_engine", listed)

    def test_standalone_minichess_computes(self):
        app = load("minichess.py")
        press(app, key="example_3 in a row")
        press(app, key="compute")
        self.assertEqual([m.value for m in app.metric], ["3", "7"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
