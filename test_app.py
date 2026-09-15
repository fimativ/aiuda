"""Checks for the workshop app: python3 -m unittest -v test_app.py"""
import math
import unittest
from collections import deque

from app import (CORE, CORE_RADIUS, HERE_FILL, MAX_TARGETS, QUESTIONS,
                 SECTORS, START, archetype, compass_figure, fewest_moves, moves_from,
                 position, trail)


def knight_distance(start, target):
    """An independent breadth-first distance, written without the solver."""
    queue, seen = deque([(start, 0)]), {start}
    while queue:
        cell, depth = queue.popleft()
        if cell == target:
            return depth
        for other in range(64):
            if sorted((abs(cell // 8 - other // 8), abs(cell % 8 - other % 8))) == [1, 2] \
                    and other not in seen:
                seen.add(other)
                queue.append((other, depth + 1))


def square(name):
    return (int(name[1]) - 1) * 8 + "abcdefgh".index(name[0])


class SolverTests(unittest.TestCase):
    def test_boards_from_the_slides(self):
        for names, expected in [(("b1", "c1"), (2, 5)), (("b1", "c1", "d1"), (3, 7)),
                                (("b1", "c1", "d1", "e1"), (4, 9)),
                                (("b2", "c3", "d4"), (6, 6))]:
            targets = tuple(sorted(map(square, names)))
            pair = (fewest_moves(START, targets, "rook"),
                    fewest_moves(START, targets, "knight"))
            self.assertEqual(pair, expected, names)

    def test_empty_board_is_zero(self):
        self.assertEqual(fewest_moves(START, (), "rook"), 0)
        self.assertEqual(fewest_moves(START, (), "knight"), 0)

    def test_every_single_target(self):
        for target in range(1, 64):
            self.assertEqual(fewest_moves(0, (target,), "rook"),
                             1 if target // 8 == 0 or target % 8 == 0 else 2)
            self.assertEqual(fewest_moves(0, (target,), "knight"),
                             knight_distance(0, target))

    def test_rook_is_blocked_but_may_capture(self):
        self.assertIn(1, moves_from(0, {1, 3}, "rook"))
        self.assertNotIn(2, moves_from(0, {1, 3}, "rook"))
        self.assertIn(17, moves_from(0, {1, 8}, "knight"))

    def test_full_board_is_fast_enough_to_be_interactive(self):
        import time
        targets = tuple(sorted(range(1, MAX_TARGETS + 1)))
        started = time.perf_counter()
        for piece in ("rook", "knight"):
            fewest_moves.cache_clear()
            self.assertGreaterEqual(fewest_moves(START, targets, piece), MAX_TARGETS)
        self.assertLess(time.perf_counter() - started, 3.0)


class SurveyTests(unittest.TestCase):
    def test_shape_of_the_instrument(self):
        self.assertEqual(len(QUESTIONS), 12)
        for prompt, options in QUESTIONS:
            self.assertEqual(len(options), 4, prompt)
            for text, x, y in options:
                self.assertTrue(text and isinstance(x, int) and isinstance(y, int))
                self.assertLessEqual(max(abs(x), abs(y)), 2)

    def test_the_origin_is_the_core(self):
        self.assertEqual(position([]), (0, 0))
        self.assertEqual(archetype(0, 0), CORE)

    def test_each_sector_claims_its_own_angle(self):
        for centre, name, title, _ in SECTORS:
            for offset in (-22, 0, 22):
                angle = math.radians(centre + offset)
                radius = CORE_RADIUS + 5
                found = archetype(radius * math.cos(angle), radius * math.sin(angle))
                self.assertEqual(found[0], name, f"{centre}{offset:+}")

    def test_the_core_boundary_is_exactly_the_radius(self):
        self.assertEqual(archetype(CORE_RADIUS - 0.1, 0), CORE)
        self.assertNotEqual(archetype(CORE_RADIUS, 0), CORE)

    def test_no_answer_can_leave_the_drawn_map(self):
        """However far a set of answers reaches, the point stays inside the map."""
        furthest = max(sum(max(x * math.cos(t) + y * math.sin(t) for _, x, y in options)
                           for _, options in QUESTIONS)
                       for t in (math.radians(d) for d in range(360)))
        for radius in (0, 1, CORE_RADIUS, 10, 20, furthest):
            point = (radius / math.sqrt(2), radius / math.sqrt(2))
            figure = compass_figure([(0, 0), point], reveal=True)
            wedges = [t for t in figure.data if t.fill == "toself"]
            rim = max(math.hypot(a, b) for t in wedges for a, b in zip(t.x, t.y))
            self.assertLess(radius, rim, f"a point at radius {radius:.1f} escapes the map")

    def test_the_trail_starts_at_the_origin_and_ends_at_the_score(self):
        picks = [0] * 12
        path = trail(picks)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], position(picks))
        self.assertEqual(len(path), 13)

    def test_every_region_is_reachable_by_some_set_of_answers(self):
        import random
        rng = random.Random(0)
        found = set()
        for _ in range(40000):
            picks = [rng.randrange(4) for _ in QUESTIONS]
            found.add(archetype(*position(picks))[0])
        self.assertEqual(len(found), 9, sorted(found))


class MapTests(unittest.TestCase):
    def highlighted(self, figure):
        """Every region drawn in the 'you are here' fill, sectors and core alike."""
        found = [t.fillcolor for t in figure.data if t.fillcolor == HERE_FILL]
        found += [s.fillcolor for s in figure.layout.shapes if s.fillcolor == HERE_FILL]
        return found

    def test_exactly_one_region_is_highlighted(self):
        """The landed region must stand out, and nothing else with it."""
        corners = [(0, 0)] + [((CORE_RADIUS + 6) * math.cos(math.radians(c)),
                               (CORE_RADIUS + 6) * math.sin(math.radians(c)))
                              for c, _, _, _ in SECTORS]
        for x, y in corners:
            figure = compass_figure([(0, 0), (x, y)], reveal=True)
            self.assertEqual(len(self.highlighted(figure)), 1, f"at ({x:.0f},{y:.0f})")

    def test_nothing_is_revealed_before_the_last_answer(self):
        figure = compass_figure([(0, 0), (2, 2), (2, 0)], reveal=False)
        self.assertEqual(self.highlighted(figure), [])
        self.assertEqual([a.text for a in figure.layout.annotations], [])

    def test_the_map_names_every_region_except_the_one_you_are_in(self):
        """Your own region is named in the heading, so the map leaves it clear."""
        every = {n for _, n, _, _ in SECTORS} | {CORE[0]}
        for x, y in [(0, 0), (20, 20), (-20, 0), (0, -20), (20, 0)]:
            figure = compass_figure([(0, 0), (x, y)], reveal=True)
            shown = {a.text.replace("<br>", " ").replace(" LEE", "-LEE")
                     for a in figure.layout.annotations}
            self.assertEqual(shown, every - {archetype(x, y)[0]}, f"({x},{y})")


class AppTests(unittest.TestCase):
    def run_app(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file("app.py", default_timeout=60).run()
        self.assertFalse(app.exception)
        return app

    def press(self, app, key):
        next(b for b in app.button if b.key == key).click().run()
        self.assertFalse(app.exception)
        return app

    def test_board_place_compute_reset(self):
        app = self.run_app()
        self.assertEqual(len({b.key for b in app.button if b.key.startswith("sq_")}), 64)
        for name in ("b1", "c1", "d1"):
            self.press(app, f"sq_{square(name)}")
        self.press(app, "compute")
        self.assertEqual(app.session_state["result"], (3, 7))
        self.press(app, "reset")
        self.assertEqual(app.session_state["targets"], set())
        self.assertIsNone(app.session_state["result"])

    def test_tapping_a_target_removes_it(self):
        app = self.run_app()
        self.press(app, "sq_9")
        self.assertIn(9, app.session_state["targets"])
        self.press(app, "sq_9")
        self.assertNotIn(9, app.session_state["targets"])

    def test_the_marked_corner_stays_empty_and_the_board_stays_whole(self):
        app = self.run_app()
        self.press(app, f"sq_{START}")
        self.assertEqual(app.session_state["targets"], set())
        self.assertEqual(len({b.key for b in app.button if b.key.startswith("sq_")}), 64)

    def test_the_cap_holds(self):
        app = self.run_app()
        free = [c for c in range(1, 64)][:MAX_TARGETS + 1]
        for cell in free:
            self.press(app, f"sq_{cell}")
        self.assertEqual(len(app.session_state["targets"]), MAX_TARGETS)
        self.assertTrue(app.session_state["full"])

    def test_editing_the_board_retires_the_numbers(self):
        app = self.run_app()
        self.press(app, "sq_9")
        self.press(app, "compute")
        self.assertIsNotNone(app.session_state["result"])
        self.press(app, "sq_18")
        self.assertIsNone(app.session_state["result"])

    def test_compass_answers_back_and_restart(self):
        app = self.run_app()
        self.press(app, "opt_0_0")
        self.assertEqual(app.session_state["picks"], [0])
        self.press(app, "back")
        self.assertEqual(app.session_state["picks"], [])
        for index in range(12):
            self.press(app, f"opt_{index}_0")
        self.assertEqual(len(app.session_state["picks"]), 12)
        self.assertTrue(any("CURIE" in h.value or h.value.isupper() for h in app.markdown
                            if h.value))
        self.press(app, "again")
        self.assertEqual(app.session_state["picks"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
