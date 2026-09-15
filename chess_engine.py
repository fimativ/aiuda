"""Exact, inspectable minimum-capture solver. No AI, no network, no randomness.

A state is (square the piece stands on, bit mask of targets still on the board).
Breadth-first search visits states in nondecreasing move count, and every edge
costs exactly one legal move, so the first completed state proves the minimum.

The public helpers are deliberately small and total: every function either
returns a well-formed value or raises ValueError with a readable message.
"""
from collections import deque
from functools import lru_cache

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
