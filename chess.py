import json
import math
import os
import random
import tkinter as tk
import time
import winsound
from dataclasses import dataclass
from tkinter import filedialog, messagebox

BOARD = 8
SQ = 78
SIDE = BOARD * SQ
PANEL = 330
WIDTH = SIDE + PANEL
HEIGHT = SIDE

LIGHT = "#f0d9b5"
DARK = "#b58863"
SELECT = "#f7ec6e"
MOVE = "#7db46c"
CAPTURE = "#d95f59"
LAST = "#9cc5ff"
CHECK = "#f05a5a"
INK = "#202020"
WHITE = "w"
BLACK = "b"

THEMES = [
    ("Classic", "#f0d9b5", "#b58863", "#25211d", "#f1c86b"),
    ("Blue", "#dee9f6", "#6f95bd", "#192532", "#8fc7ff"),
    ("Green", "#e8ecd1", "#779954", "#20281b", "#c7df83"),
    ("Dark", "#b9b9b9", "#4c4c4c", "#171717", "#e7c46f"),
]

STATS_FILE = os.path.join(os.path.dirname(__file__), "chess_stats.json")

UNICODE = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

@dataclass
class Move:
    start: tuple
    end: tuple
    piece: str
    captured: str = ""
    promotion: str = ""
    castle: bool = False
    en_passant: bool = False

class ChessGame:
    def __init__(self):
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.turn = WHITE
        self.castling = {"K": True, "Q": True, "k": True, "q": True}
        self.en_passant = None
        self.history = []
        self.last_move = None
        self.result = ""
        self.move_log = []

    def clone(self):
        other = ChessGame()
        other.board = [row[:] for row in self.board]
        other.turn = self.turn
        other.castling = self.castling.copy()
        other.en_passant = self.en_passant
        other.history = list(self.history)
        other.last_move = self.last_move
        other.result = self.result
        other.move_log = list(self.move_log)
        return other

    def square_name(self, square):
        r, c = square
        return "abcdefgh"[c] + str(8 - r)

    def move_name(self, move):
        if move.castle:
            return "O-O" if move.end[1] == 6 else "O-O-O"
        name = ""
        if move.piece.upper() != "P":
            name += move.piece.upper()
        elif move.captured:
            name += "abcdefgh"[move.start[1]]
        if move.captured:
            name += "x"
        name += self.square_name(move.end)
        if move.promotion:
            name += "=" + move.promotion.upper()
        if move.en_passant:
            name += " e.p."
        return name

    def captured_pieces(self, color):
        starting = "PPPPPPPPNNBBRRQK" if color == WHITE else "ppppppppnnbbrrqk"
        remaining = "".join(piece for row in self.board for piece in row if self.color(piece) == color)
        captured = []
        for piece in starting:
            if remaining.count(piece) < starting.count(piece) - captured.count(piece):
                captured.append(piece)
        return sorted(captured, key=lambda p: VALUES[p.upper()])

    def material_score(self):
        white = sum(VALUES[p.upper()] for row in self.board for p in row if self.color(p) == WHITE)
        black = sum(VALUES[p.upper()] for row in self.board for p in row if self.color(p) == BLACK)
        return white - black

    def export_state(self):
        return {
            "board": ["".join(row) for row in self.board],
            "turn": self.turn,
            "castling": self.castling,
            "en_passant": self.en_passant,
            "move_log": self.move_log,
            "result": self.result,
        }

    def import_state(self, state):
        self.board = [list(row) for row in state["board"]]
        self.turn = state.get("turn", WHITE)
        self.castling = state.get("castling", {"K": False, "Q": False, "k": False, "q": False})
        ep = state.get("en_passant")
        self.en_passant = tuple(ep) if ep else None
        self.move_log = list(state.get("move_log", []))
        self.result = state.get("result", "")
        self.history = []
        self.last_move = None

    def to_fen(self):
        rows = []
        for row in self.board:
            out = ""
            empty = 0
            for piece in row:
                if piece == ".":
                    empty += 1
                else:
                    if empty:
                        out += str(empty)
                        empty = 0
                    out += piece
            if empty:
                out += str(empty)
            rows.append(out)
        castling = "".join(k for k in "KQkq" if self.castling.get(k)) or "-"
        ep = self.square_name(self.en_passant) if self.en_passant else "-"
        return f"{'/'.join(rows)} {'w' if self.turn == WHITE else 'b'} {castling} {ep} 0 1"

    def load_fen(self, fen):
        parts = fen.strip().split()
        if len(parts) < 4:
            raise ValueError("FEN me board, turn, castling aur en-passant fields chahiye.")
        rows = parts[0].split("/")
        if len(rows) != 8:
            raise ValueError("FEN board me 8 rows honi chahiye.")
        board = []
        valid = set("prnbqkPRNBQK")
        for row in rows:
            out = []
            for ch in row:
                if ch.isdigit():
                    out.extend("." for _ in range(int(ch)))
                elif ch in valid:
                    out.append(ch)
                else:
                    raise ValueError("FEN me invalid piece hai.")
            if len(out) != 8:
                raise ValueError("Har FEN row me 8 squares hone chahiye.")
            board.append(out)
        self.board = board
        self.turn = WHITE if parts[1] == "w" else BLACK
        rights = parts[2]
        self.castling = {k: rights != "-" and k in rights for k in "KQkq"}
        self.en_passant = None if parts[3] == "-" else (8 - int(parts[3][1]), "abcdefgh".index(parts[3][0]))
        self.history = []
        self.last_move = None
        self.move_log = []
        self.result = ""

    def color(self, piece):
        if piece == ".":
            return None
        return WHITE if piece.isupper() else BLACK

    def enemy(self, color):
        return BLACK if color == WHITE else WHITE

    def inside(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def king_pos(self, color):
        target = "K" if color == WHITE else "k"
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def square_attacked(self, r, c, by_color):
        pawn_dir = -1 if by_color == WHITE else 1
        for dc in (-1, 1):
            rr, cc = r - pawn_dir, c + dc
            if self.inside(rr, cc):
                piece = self.board[rr][cc]
                if piece == ("P" if by_color == WHITE else "p"):
                    return True

        for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
            rr, cc = r + dr, c + dc
            if self.inside(rr, cc):
                piece = self.board[rr][cc]
                if piece == ("N" if by_color == WHITE else "n"):
                    return True

        for dr, dc, attackers in (
            (-1, 0, "RQ"),
            (1, 0, "RQ"),
            (0, -1, "RQ"),
            (0, 1, "RQ"),
            (-1, -1, "BQ"),
            (-1, 1, "BQ"),
            (1, -1, "BQ"),
            (1, 1, "BQ"),
        ):
            rr, cc = r + dr, c + dc
            while self.inside(rr, cc):
                piece = self.board[rr][cc]
                if piece != ".":
                    if self.color(piece) == by_color and piece.upper() in attackers:
                        return True
                    break
                rr += dr
                cc += dc

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if self.inside(rr, cc):
                    piece = self.board[rr][cc]
                    if piece == ("K" if by_color == WHITE else "k"):
                        return True
        return False

    def in_check(self, color):
        king = self.king_pos(color)
        return bool(king and self.square_attacked(king[0], king[1], self.enemy(color)))

    def pseudo_moves(self, color):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if self.color(piece) != color:
                    continue
                kind = piece.upper()
                if kind == "P":
                    self.pawn_moves(r, c, piece, moves)
                elif kind == "N":
                    self.jump_moves(r, c, piece, moves, ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)))
                elif kind == "B":
                    self.slide_moves(r, c, piece, moves, ((-1, -1), (-1, 1), (1, -1), (1, 1)))
                elif kind == "R":
                    self.slide_moves(r, c, piece, moves, ((-1, 0), (1, 0), (0, -1), (0, 1)))
                elif kind == "Q":
                    self.slide_moves(r, c, piece, moves, ((-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)))
                elif kind == "K":
                    self.king_moves(r, c, piece, moves)
        return moves

    def pawn_moves(self, r, c, piece, moves):
        color = self.color(piece)
        direction = -1 if color == WHITE else 1
        start_row = 6 if color == WHITE else 1
        promo_row = 0 if color == WHITE else 7
        one = r + direction
        if self.inside(one, c) and self.board[one][c] == ".":
            self.add_pawn_move(r, c, one, c, piece, moves, promo_row)
            two = r + direction * 2
            if r == start_row and self.board[two][c] == ".":
                moves.append(Move((r, c), (two, c), piece))
        for dc in (-1, 1):
            rr, cc = r + direction, c + dc
            if not self.inside(rr, cc):
                continue
            target = self.board[rr][cc]
            if target != "." and self.color(target) != color:
                self.add_pawn_move(r, c, rr, cc, piece, moves, promo_row, target)
            if self.en_passant == (rr, cc):
                moves.append(Move((r, c), (rr, cc), piece, "p" if color == WHITE else "P", en_passant=True))

    def add_pawn_move(self, r, c, rr, cc, piece, moves, promo_row, captured=""):
        if rr == promo_row:
            for promo in ("Q", "R", "B", "N"):
                moves.append(Move((r, c), (rr, cc), piece, captured, promo if piece.isupper() else promo.lower()))
        else:
            moves.append(Move((r, c), (rr, cc), piece, captured))

    def jump_moves(self, r, c, piece, moves, offsets):
        color = self.color(piece)
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if self.inside(rr, cc) and self.color(self.board[rr][cc]) != color:
                target = self.board[rr][cc]
                moves.append(Move((r, c), (rr, cc), piece, "" if target == "." else target))

    def slide_moves(self, r, c, piece, moves, directions):
        color = self.color(piece)
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            while self.inside(rr, cc):
                target = self.board[rr][cc]
                if target == ".":
                    moves.append(Move((r, c), (rr, cc), piece))
                else:
                    if self.color(target) != color:
                        moves.append(Move((r, c), (rr, cc), piece, target))
                    break
                rr += dr
                cc += dc

    def king_moves(self, r, c, piece, moves):
        self.jump_moves(r, c, piece, moves, ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)))
        color = self.color(piece)
        if self.in_check(color):
            return
        row = 7 if color == WHITE else 0
        enemy = self.enemy(color)
        if color == WHITE:
            if self.castling["K"] and self.board[row][7] == "R" and self.board[row][5] == "." and self.board[row][6] == ".":
                if not self.square_attacked(row, 5, enemy) and not self.square_attacked(row, 6, enemy):
                    moves.append(Move((r, c), (row, 6), piece, castle=True))
            if self.castling["Q"] and self.board[row][0] == "R" and self.board[row][1] == "." and self.board[row][2] == "." and self.board[row][3] == ".":
                if not self.square_attacked(row, 2, enemy) and not self.square_attacked(row, 3, enemy):
                    moves.append(Move((r, c), (row, 2), piece, castle=True))
        else:
            if self.castling["k"] and self.board[row][7] == "r" and self.board[row][5] == "." and self.board[row][6] == ".":
                if not self.square_attacked(row, 5, enemy) and not self.square_attacked(row, 6, enemy):
                    moves.append(Move((r, c), (row, 6), piece, castle=True))
            if self.castling["q"] and self.board[row][0] == "r" and self.board[row][1] == "." and self.board[row][2] == "." and self.board[row][3] == ".":
                if not self.square_attacked(row, 2, enemy) and not self.square_attacked(row, 3, enemy):
                    moves.append(Move((r, c), (row, 2), piece, castle=True))

    def legal_moves(self, color=None):
        color = color or self.turn
        legal = []
        for move in self.pseudo_moves(color):
            trial = self.clone()
            trial.apply_move(move, save=False)
            if not trial.in_check(color):
                legal.append(move)
        return legal

    def apply_move(self, move, save=True):
        if save:
            self.history.append((
                [row[:] for row in self.board],
                self.turn,
                self.castling.copy(),
                self.en_passant,
                self.last_move,
                self.result,
                list(self.move_log),
            ))
            notation = self.move_name(move)
        sr, sc = move.start
        er, ec = move.end
        self.board[sr][sc] = "."
        placed = move.promotion or move.piece
        self.board[er][ec] = placed

        if move.en_passant:
            cap_row = er + (1 if self.color(move.piece) == WHITE else -1)
            self.board[cap_row][ec] = "."

        if move.castle:
            if ec == 6:
                self.board[er][5] = self.board[er][7]
                self.board[er][7] = "."
            else:
                self.board[er][3] = self.board[er][0]
                self.board[er][0] = "."

        self.update_castling(move)
        self.en_passant = None
        if move.piece.upper() == "P" and abs(er - sr) == 2:
            self.en_passant = ((er + sr) // 2, sc)

        self.last_move = move
        self.turn = self.enemy(self.turn)
        if save:
            self.update_result()
            if self.result.startswith("Checkmate"):
                notation += "#"
            elif self.in_check(self.turn):
                notation += "+"
            self.move_log.append(notation)

    def update_castling(self, move):
        sr, sc = move.start
        er, ec = move.end
        piece = move.piece
        if piece == "K":
            self.castling["K"] = self.castling["Q"] = False
        elif piece == "k":
            self.castling["k"] = self.castling["q"] = False
        elif piece == "R" and (sr, sc) == (7, 0):
            self.castling["Q"] = False
        elif piece == "R" and (sr, sc) == (7, 7):
            self.castling["K"] = False
        elif piece == "r" and (sr, sc) == (0, 0):
            self.castling["q"] = False
        elif piece == "r" and (sr, sc) == (0, 7):
            self.castling["k"] = False

        if (er, ec) == (7, 0):
            self.castling["Q"] = False
        elif (er, ec) == (7, 7):
            self.castling["K"] = False
        elif (er, ec) == (0, 0):
            self.castling["q"] = False
        elif (er, ec) == (0, 7):
            self.castling["k"] = False

    def undo(self):
        if not self.history:
            return
        self.board, self.turn, self.castling, self.en_passant, self.last_move, self.result, self.move_log = self.history.pop()

    def update_result(self):
        moves = self.legal_moves(self.turn)
        if moves:
            self.result = ""
        elif self.in_check(self.turn):
            winner = "White" if self.turn == BLACK else "Black"
            self.result = f"Checkmate - {winner} wins"
        else:
            self.result = "Stalemate"

class ChessAI:
    def __init__(self, color=BLACK, depth=3):
        self.color = color
        self.depth = depth

    def choose(self, game):
        moves = game.legal_moves(self.color)
        if not moves:
            return None
        moves = self.ordered_moves(game, moves)
        best_move = moves[0]
        best_score = -math.inf
        alpha = -math.inf
        beta = math.inf
        for move in moves:
            trial = game.clone()
            trial.apply_move(move, save=False)
            score = -self.search(trial, self.depth - 1, -beta, -alpha, game.enemy(self.color))
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
        return best_move

    def search(self, game, depth, alpha, beta, color):
        moves = game.legal_moves(color)
        if not moves:
            return -100000 if game.in_check(color) else 0
        if depth == 0:
            return self.evaluate(game, color)
        moves = self.ordered_moves(game, moves)
        best = -math.inf
        enemy = game.enemy(color)
        for move in moves:
            trial = game.clone()
            trial.apply_move(move, save=False)
            score = -self.search(trial, depth - 1, -beta, -alpha, enemy)
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best

    def ordered_moves(self, game, moves):
        decorated = []
        for move in moves:
            score = 0
            if move.captured:
                score += 10 * VALUES[move.captured.upper()] - VALUES[move.piece.upper()]
            if move.promotion:
                score += VALUES[move.promotion.upper()]
            if move.castle:
                score += 45
            trial = game.clone()
            trial.apply_move(move, save=False)
            if trial.in_check(trial.turn):
                score += 35
            decorated.append((score + random.random(), move))
        decorated.sort(key=lambda item: item[0], reverse=True)
        return [move for _, move in decorated]

    def evaluate(self, game, perspective):
        if game.result:
            if "Checkmate" in game.result:
                winner_color = WHITE if "White" in game.result else BLACK
                return 100000 if winner_color == perspective else -100000
            return 0

        score = 0
        for r in range(8):
            for c in range(8):
                piece = game.board[r][c]
                if piece == ".":
                    continue
                val = VALUES[piece.upper()]
                if piece.upper() == "P":
                    table = PAWN_TABLE[r if piece.islower() else 7 - r][c]
                    val += table
                elif piece.upper() == "N":
                    table = KNIGHT_TABLE[r if piece.islower() else 7 - r][c]
                    val += table
                if game.color(piece) == perspective:
                    score += val
                else:
                    score -= val
        score += 4 * (len(game.legal_moves(perspective)) - len(game.legal_moves(game.enemy(perspective))))
        if game.in_check(game.enemy(perspective)):
            score += 30
        if game.in_check(perspective):
            score -= 30
        return score

class ChessUI:
    def __init__(self, root):
        self.root = root
        self.root.title("High Level Python Chess")
        self.game = ChessGame()
        self.ai = ChessAI(BLACK, 3)
        self.ai_depth = 3
        self.selected = None
        self.legal_for_selected = []
        self.hint_move = None
        self.ai_enabled = tk.BooleanVar(value=True)
        self.thinking = False
        self.sound_enabled = True
        self.piece_size = 52
        self.theme_index = 0
        self.show_coords = True
        self.flipped = False
        self.timer_presets = [("1+0", 60), ("3+2", 180), ("10+0", 600), ("30+0", 1800)]
        self.timer_index = 2
        self.base_seconds = self.timer_presets[self.timer_index][1]
        self.arrows = []
        self.arrow_start = None
        self.stats = self.load_stats()
        self._recorded_result = None
        self.dragging = False
        self.drag_start = None
        self.drag_xy = None
        self.fullscreen = False
        self.white_seconds = self.base_seconds
        self.black_seconds = self.base_seconds
        self.last_tick = time.time()

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#ede7dc", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<Button-3>", self.arrow_down)
        self.canvas.bind("<ButtonRelease-3>", self.arrow_up)
        self.root.bind("<u>", lambda event: self.undo_pair())
        self.root.bind("<r>", lambda event: self.reset())
        self.root.bind("<h>", lambda event: self.make_hint())
        self.root.bind("<s>", lambda event: self.save_game())
        self.root.bind("<l>", lambda event: self.load_game())
        self.root.bind("<t>", lambda event: self.next_theme())
        self.root.bind("<f>", lambda event: self.flip_board())
        self.root.bind("<c>", lambda event: self.toggle_coords())
        self.root.bind("<p>", lambda event: self.export_pgn())
        self.root.bind("<Control-f>", lambda event: self.ask_fen())
        self.root.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda event: self.exit_fullscreen())
        self.root.bind("<plus>", lambda event: self.change_piece_size(4))
        self.root.bind("<minus>", lambda event: self.change_piece_size(-4))
        self.draw()
        self.tick()

    def reset(self):
        self.game = ChessGame()
        self.ai = ChessAI(BLACK, self.ai_depth)
        self.selected = None
        self.legal_for_selected = []
        self.hint_move = None
        self.thinking = False
        self.white_seconds = self.base_seconds
        self.black_seconds = self.base_seconds
        self.arrows = []
        self._recorded_result = None
        self.last_tick = time.time()
        self.play_sound("start")
        self.draw()

    def load_stats(self):
        default = {"white_wins": 0, "black_wins": 0, "draws": 0, "games": 0}
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            default.update({k: int(data.get(k, v)) for k, v in default.items()})
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        return default

    def save_stats(self):
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except OSError:
            pass

    def record_result(self):
        if getattr(self, "_recorded_result", None) == self.game.result or not self.game.result:
            return
        self._recorded_result = self.game.result
        self.stats["games"] += 1
        if "White wins" in self.game.result:
            self.stats["white_wins"] += 1
        elif "Black wins" in self.game.result:
            self.stats["black_wins"] += 1
        else:
            self.stats["draws"] += 1
        self.save_stats()

    def theme(self):
        return THEMES[self.theme_index]

    def next_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.draw()

    def flip_board(self):
        self.flipped = not self.flipped
        self.draw()

    def toggle_coords(self):
        self.show_coords = not self.show_coords
        self.draw()

    def next_timer(self):
        self.timer_index = (self.timer_index + 1) % len(self.timer_presets)
        self.base_seconds = self.timer_presets[self.timer_index][1]
        self.white_seconds = self.base_seconds
        self.black_seconds = self.base_seconds
        self.update_clock_anchor()
        self.draw()

    def ask_fen(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Load FEN")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Paste FEN position", font=("Segoe UI", 11, "bold")).pack(padx=14, pady=(12, 6))
        entry = tk.Entry(dialog, width=82)
        entry.insert(0, self.game.to_fen())
        entry.pack(padx=14, pady=6)
        def load():
            try:
                self.game.load_fen(entry.get())
                self.selected = None
                self.legal_for_selected = []
                self.hint_move = None
                self.arrows = []
                self.update_clock_anchor()
                dialog.destroy()
                self.draw()
            except ValueError as exc:
                messagebox.showerror("Bad FEN", str(exc))
        tk.Button(dialog, text="Load Position", command=load).pack(pady=(4, 12))
        entry.focus_set()
        self.root.wait_window(dialog)

    def export_pgn(self):
        path = filedialog.asksaveasfilename(
            title="Export PGN",
            defaultextension=".pgn",
            filetypes=[("PGN", "*.pgn"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        lines = ['[Event "Python Chess Pro"]', '[Site "Local"]', '[Result "*"]', ""]
        moves = []
        for idx in range(0, len(self.game.move_log), 2):
            move_no = idx // 2 + 1
            white = self.game.move_log[idx]
            black = self.game.move_log[idx + 1] if idx + 1 < len(self.game.move_log) else ""
            moves.append(f"{move_no}. {white}" + (f" {black}" if black else ""))
        lines.append(" ".join(moves) or "*")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.play_sound("hint")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def save_game(self):
        path = filedialog.asksaveasfilename(
            title="Save chess game",
            defaultextension=".json",
            filetypes=[("Chess save", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        state = self.game.export_state()
        state.update({
            "white_seconds": self.white_seconds,
            "black_seconds": self.black_seconds,
            "ai_depth": self.ai_depth,
            "ai_enabled": self.ai_enabled.get(),
            "piece_size": self.piece_size,
            "theme_index": self.theme_index,
            "show_coords": self.show_coords,
            "flipped": self.flipped,
            "timer_index": self.timer_index,
            "arrows": self.arrows,
        })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        self.play_sound("hint")

    def load_game(self):
        path = filedialog.askopenfilename(
            title="Load chess game",
            filetypes=[("Chess save", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.game.import_state(state)
            self.white_seconds = int(state.get("white_seconds", self.white_seconds))
            self.black_seconds = int(state.get("black_seconds", self.black_seconds))
            self.ai_depth = int(state.get("ai_depth", self.ai_depth))
            self.ai = ChessAI(BLACK, self.ai_depth)
            self.ai_enabled.set(bool(state.get("ai_enabled", self.ai_enabled.get())))
            self.piece_size = int(state.get("piece_size", self.piece_size))
            self.theme_index = int(state.get("theme_index", self.theme_index)) % len(THEMES)
            self.show_coords = bool(state.get("show_coords", self.show_coords))
            self.flipped = bool(state.get("flipped", self.flipped))
            self.timer_index = int(state.get("timer_index", self.timer_index)) % len(self.timer_presets)
            self.base_seconds = self.timer_presets[self.timer_index][1]
            self.arrows = [(tuple(a), tuple(b)) for a, b in state.get("arrows", [])]
            self.selected = None
            self.legal_for_selected = []
            self.hint_move = None
            self.update_clock_anchor()
            self.play_sound("start")
            self.draw()
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            messagebox.showerror("Load failed", f"Game save load nahi hua:\n{exc}")

    def undo_pair(self):
        if self.thinking:
            return
        self.game.undo()
        if self.ai_enabled.get() and self.game.turn == BLACK:
            self.game.undo()
        self.selected = None
        self.legal_for_selected = []
        self.hint_move = None
        self.play_sound("undo")
        self.draw()

    def tick(self):
        now = time.time()
        elapsed = int(now - self.last_tick)
        if elapsed > 0:
            self.last_tick = now
            if not self.game.result:
                if self.game.turn == WHITE:
                    self.white_seconds = max(0, self.white_seconds - elapsed)
                    if self.white_seconds == 0:
                        self.game.result = "Time - Black wins"
                        self.record_result()
                else:
                    self.black_seconds = max(0, self.black_seconds - elapsed)
                    if self.black_seconds == 0:
                        self.game.result = "Time - White wins"
                        self.record_result()
            self.draw()
        self.root.after(250, self.tick)

    def update_clock_anchor(self):
        self.last_tick = time.time()

    def screen_to_square(self, x, y):
        if not (0 <= x < SIDE and 0 <= y < SIDE):
            return None
        row, col = y // SQ, x // SQ
        if self.flipped:
            row, col = 7 - row, 7 - col
        return (row, col)

    def square_center(self, square):
        row, col = square
        if self.flipped:
            row, col = 7 - row, 7 - col
        return col * SQ + SQ // 2, row * SQ + SQ // 2

    def square_top_left(self, square):
        row, col = square
        if self.flipped:
            row, col = 7 - row, 7 - col
        return col * SQ, row * SQ

    def play_sound(self, kind):
        if not self.sound_enabled:
            return
        sounds = {
            "move": (620, 55),
            "capture": (260, 80),
            "check": (880, 120),
            "mate": (940, 90),
            "hint": (740, 55),
            "undo": (420, 45),
            "start": (520, 50),
        }
        freq, duration = sounds.get(kind, sounds["move"])
        try:
            winsound.Beep(freq, duration)
        except RuntimeError:
            pass

    def sound_for_move(self, move):
        if self.game.result:
            return "mate"
        if self.game.in_check(self.game.turn):
            return "check"
        if move.captured or move.en_passant:
            return "capture"
        return "move"

    def change_piece_size(self, delta):
        self.piece_size = max(40, min(68, self.piece_size + delta))
        self.draw()

    def click(self, event):
        if event.x >= SIDE or self.thinking or self.game.result:
            self.panel_click(event.x, event.y)
            return
        square = self.screen_to_square(event.x, event.y)
        if not square:
            return
        row, col = square
        piece = self.game.board[row][col]
        if self.game.color(piece) == self.game.turn and (not self.ai_enabled.get() or self.game.turn == WHITE):
            self.drag_start = (row, col)
            self.drag_xy = (event.x, event.y)
        if self.selected:
            chosen = self.find_move(self.selected, (row, col))
            if chosen:
                self.perform_player_move(chosen)
                return

        if self.game.color(piece) == self.game.turn and (not self.ai_enabled.get() or self.game.turn == WHITE):
            self.selected = (row, col)
            self.legal_for_selected = [m for m in self.game.legal_moves() if m.start == self.selected]
        else:
            self.selected = None
            self.legal_for_selected = []
        self.draw()

    def drag(self, event):
        if not self.drag_start or self.thinking or self.game.result:
            return
        if self.drag_xy and (abs(event.x - self.drag_xy[0]) > 6 or abs(event.y - self.drag_xy[1]) > 6):
            self.dragging = True
            self.drag_xy = (event.x, event.y)
            self.draw()

    def release(self, event):
        if not self.dragging or not self.drag_start:
            self.dragging = False
            self.drag_start = None
            self.drag_xy = None
            return
        start = self.drag_start
        self.dragging = False
        self.drag_start = None
        self.drag_xy = None
        end = self.screen_to_square(event.x, event.y)
        if end:
            self.legal_for_selected = [m for m in self.game.legal_moves() if m.start == start]
            move = self.find_move(start, end)
            if move:
                self.perform_player_move(move)
                return
        self.draw()

    def arrow_down(self, event):
        self.arrow_start = self.screen_to_square(event.x, event.y)

    def arrow_up(self, event):
        end = self.screen_to_square(event.x, event.y)
        if self.arrow_start and end:
            arrow = (self.arrow_start, end)
            if arrow in self.arrows:
                self.arrows.remove(arrow)
            else:
                self.arrows.append(arrow)
        self.arrow_start = None
        self.draw()

    def perform_player_move(self, move):
        if move.promotion:
            chosen_piece = self.choose_promotion(move.piece.isupper())
            move = Move(move.start, move.end, move.piece, move.captured, chosen_piece, move.castle, move.en_passant)
        self.update_clock_anchor()
        self.game.apply_move(move)
        self.play_sound(self.sound_for_move(move))
        self.record_result()
        self.selected = None
        self.legal_for_selected = []
        self.hint_move = None
        self.draw()
        if self.ai_enabled.get() and self.game.turn == BLACK and not self.game.result:
            self.thinking = True
            self.draw()
            self.root.after(100, self.ai_move)

    def choose_promotion(self, white_piece):
        dialog = tk.Toplevel(self.root)
        dialog.title("Promote pawn")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        choice = {"piece": "Q" if white_piece else "q"}
        tk.Label(dialog, text="Promote pawn to", font=("Segoe UI", 12, "bold")).pack(padx=18, pady=(14, 8))
        row = tk.Frame(dialog)
        row.pack(padx=12, pady=(0, 14))
        for piece in ("Q", "R", "B", "N"):
            actual = piece if white_piece else piece.lower()
            btn = tk.Button(row, text=UNICODE[actual], font=("Segoe UI Symbol", 28), width=3,
                            command=lambda p=actual: self.finish_promotion(dialog, choice, p))
            btn.pack(side=tk.LEFT, padx=4)
        self.root.wait_window(dialog)
        return choice["piece"]

    def finish_promotion(self, dialog, choice, piece):
        choice["piece"] = piece
        dialog.destroy()

    def panel_click(self, x, y):
        if SIDE + 32 <= x <= SIDE + 292 and 158 <= y <= 196:
            self.ai_enabled.set(not self.ai_enabled.get())
            self.draw()
        elif SIDE + 32 <= x <= SIDE + 292 and 208 <= y <= 246:
            self.make_hint()
        elif SIDE + 32 <= x <= SIDE + 292 and 258 <= y <= 296:
            self.undo_pair()
        elif SIDE + 32 <= x <= SIDE + 292 and 302 <= y <= 340:
            self.reset()
        elif 350 <= y <= 384:
            if SIDE + 32 <= x <= SIDE + 114:
                self.save_game()
            elif SIDE + 122 <= x <= SIDE + 204:
                self.load_game()
            elif SIDE + 212 <= x <= SIDE + 292:
                self.next_theme()
        elif 408 <= y <= 442:
            for i, depth in enumerate((1, 2, 3, 4)):
                bx = SIDE + 32 + i * 66
                if bx <= x <= bx + 54:
                    self.ai_depth = depth
                    self.ai = ChessAI(BLACK, depth)
                    self.draw()
        elif 482 <= y <= 520:
            if SIDE + 32 <= x <= SIDE + 114:
                self.change_piece_size(-4)
            elif SIDE + 122 <= x <= SIDE + 204:
                self.change_piece_size(4)
            elif SIDE + 212 <= x <= SIDE + 292:
                self.sound_enabled = not self.sound_enabled
                self.play_sound("hint")
                self.draw()
        elif 526 <= y <= 560:
            if SIDE + 32 <= x <= SIDE + 114:
                self.next_timer()
            elif SIDE + 122 <= x <= SIDE + 204:
                self.flip_board()
            elif SIDE + 212 <= x <= SIDE + 292:
                self.toggle_coords()
        elif 566 <= y <= 600:
            if SIDE + 32 <= x <= SIDE + 114:
                self.export_pgn()
            elif SIDE + 122 <= x <= SIDE + 204:
                self.ask_fen()
            elif SIDE + 212 <= x <= SIDE + 292:
                self.game.result = "Draw agreed"
                self.record_result()
                self.draw()
        elif 604 <= y <= 622 and SIDE + 32 <= x <= SIDE + 114:
            winner = "Black" if self.game.turn == WHITE else "White"
            self.game.result = f"Resign - {winner} wins"
            self.record_result()
            self.draw()

    def ai_move(self):
        move = self.ai.choose(self.game)
        if move:
            self.update_clock_anchor()
            self.game.apply_move(move)
            self.play_sound(self.sound_for_move(move))
            self.record_result()
        self.thinking = False
        self.draw()

    def make_hint(self):
        if self.thinking or self.game.result:
            return
        if self.ai_enabled.get() and self.game.turn == BLACK:
            return
        hint_ai = ChessAI(self.game.turn, min(2, self.ai_depth))
        self.hint_move = hint_ai.choose(self.game)
        self.play_sound("hint")
        self.draw()

    def find_move(self, start, end):
        candidates = [m for m in self.legal_for_selected if m.start == start and m.end == end]
        if not candidates:
            return None
        queen = [m for m in candidates if m.promotion and m.promotion.upper() == "Q"]
        return queen[0] if queen else candidates[0]

    def draw(self):
        self.canvas.delete("all")
        self.draw_board()
        self.draw_arrows()
        self.draw_hint()
        self.draw_dragged_piece()
        self.draw_panel()

    def draw_hint(self):
        if not self.hint_move:
            return
        sr, sc = self.hint_move.start
        er, ec = self.hint_move.end
        x1, y1 = sc * SQ + SQ // 2, sr * SQ + SQ // 2
        x2, y2 = ec * SQ + SQ // 2, er * SQ + SQ // 2
        self.canvas.create_line(x1, y1, x2, y2, fill="#0e5f6f", width=5, arrow=tk.LAST, arrowshape=(18, 22, 8))

    def draw_board(self):
        _, light, dark, _, _ = self.theme()
        check_square = self.game.king_pos(self.game.turn) if self.game.in_check(self.game.turn) else None
        last = []
        if self.game.last_move:
            last = [self.game.last_move.start, self.game.last_move.end]
        move_ends = {m.end: m for m in self.legal_for_selected}

        for r in range(8):
            for c in range(8):
                x0, y0 = self.square_top_left((r, c))
                color = light if (r + c) % 2 == 0 else dark
                if (r, c) in last:
                    color = LAST
                if self.selected == (r, c):
                    color = SELECT
                if check_square == (r, c):
                    color = CHECK
                self.canvas.create_rectangle(x0, y0, x0 + SQ, y0 + SQ, fill=color, outline=color)

                if (r, c) in move_ends:
                    move = move_ends[(r, c)]
                    fill = CAPTURE if move.captured else MOVE
                    self.canvas.create_oval(x0 + 28, y0 + 28, x0 + 50, y0 + 50, fill=fill, outline="")

                piece = self.game.board[r][c]
                if piece != "." and not (self.dragging and self.drag_start == (r, c)):
                    self.draw_piece(r, c, piece)

        if self.show_coords:
            files = "hgfedcba" if self.flipped else "abcdefgh"
            ranks = "12345678" if self.flipped else "87654321"
            for i, label in enumerate(files):
                self.canvas.create_text(i * SQ + 8, SIDE - 10, text=label, fill="#423124", anchor="w", font=("Segoe UI", 10, "bold"))
                self.canvas.create_text(8, i * SQ + 12, text=ranks[i], fill="#423124", anchor="w", font=("Segoe UI", 10, "bold"))

    def draw_arrows(self):
        for start, end in self.arrows:
            x1, y1 = self.square_center(start)
            x2, y2 = self.square_center(end)
            self.canvas.create_line(x1, y1, x2, y2, fill="#d58f18", width=6, arrow=tk.LAST, arrowshape=(18, 22, 8), stipple="gray50")

    def draw_piece(self, r, c, piece):
        cx, cy = self.square_center((r, c))
        self.draw_piece_at(cx, cy, piece)

    def draw_piece_at(self, cx, cy, piece):
        symbol = UNICODE[piece]
        font = ("Segoe UI Symbol", self.piece_size, "normal")
        if piece.isupper():
            for dx, dy in ((2, 2), (-1, 1), (1, -1)):
                self.canvas.create_text(cx + dx, cy + dy, text=symbol, fill="#2b211a", font=font)
            self.canvas.create_text(cx, cy, text=symbol, fill="#fff8e8", font=font)
        else:
            self.canvas.create_text(cx + 2, cy + 2, text=symbol, fill="#f3dfbd", font=font)
            self.canvas.create_text(cx, cy, text=symbol, fill="#191614", font=font)

    def draw_dragged_piece(self):
        if not self.dragging or not self.drag_start or not self.drag_xy:
            return
        piece = self.game.board[self.drag_start[0]][self.drag_start[1]]
        if piece != ".":
            self.draw_piece_at(self.drag_xy[0], self.drag_xy[1], piece)

    def draw_panel(self):
        x = SIDE
        theme_name, _, _, panel_color, _ = self.theme()
        self.canvas.create_rectangle(x, 0, WIDTH, HEIGHT, fill=panel_color, outline="")
        self.canvas.create_text(x + 28, 28, text="PYTHON CHESS PRO", fill="#f7efe3", anchor="w", font=("Segoe UI", 19, "bold"))
        self.canvas.create_text(x + 28, 58, text=f"{theme_name} theme, smart AI, complete rules.", fill="#cabdae", anchor="w", font=("Segoe UI", 10))

        status = self.game.result or ("AI thinking..." if self.thinking else ("White to move" if self.game.turn == WHITE else "Black to move"))
        self.canvas.create_text(x + 28, 96, text=status, fill="#ffffff", anchor="w", font=("Segoe UI", 14, "bold"), width=260)
        if self.game.in_check(self.game.turn) and not self.game.result:
            self.canvas.create_text(x + 28, 122, text="Check", fill="#ffbbb6", anchor="w", font=("Segoe UI", 11, "bold"))

        self.draw_clock(x + 28, 132)

        ai_text = "Computer: ON" if self.ai_enabled.get() else "Computer: OFF"
        self.button(x + 32, 158, ai_text, 260)
        self.button(x + 32, 208, "Hint")
        self.button(x + 32, 258, "Undo")
        self.button(x + 32, 302, "New Game")

        self.button(x + 32, 350, "Save", 82)
        self.button(x + 122, 350, "Load", 82)
        self.button(x + 212, 350, "Theme", 80)

        self.canvas.create_text(x + 28, 398, text="AI Level", fill="#f7efe3", anchor="w", font=("Segoe UI", 12, "bold"))
        for i, depth in enumerate((1, 2, 3, 4)):
            bx = x + 32 + i * 66
            active = depth == self.ai_depth
            self.canvas.create_rectangle(bx, 408, bx + 54, 442, fill="#f1c86b" if active else "#3b342d", outline="#e5b958" if active else "#5b5148", width=2)
            self.canvas.create_text(bx + 27, 425, text=str(depth), fill=INK if active else "#f7efe3", font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(x + 28, 460, text="Pieces", fill="#f7efe3", anchor="w", font=("Segoe UI", 12, "bold"))
        self.button(x + 32, 482, "Small", 82)
        self.button(x + 122, 482, "Large", 82)
        sound_text = "Sound ON" if self.sound_enabled else "Sound OFF"
        self.button(x + 212, 482, sound_text, 80)

        timer_text = "Timer " + self.timer_presets[self.timer_index][0]
        self.small_button(x + 32, 526, timer_text, 82)
        self.small_button(x + 122, 526, "Flip", 82)
        self.small_button(x + 212, 526, "Coords", 80)
        self.small_button(x + 32, 566, "PGN", 82)
        self.small_button(x + 122, 566, "FEN", 82)
        self.small_button(x + 212, 566, "Draw", 80)
        self.small_button(x + 32, 604, "Resign", 82, 18)

        self.draw_captured(x + 172, 534)
        self.draw_stats(x + 122, 604)

    def draw_clock(self, x, y):
        self.canvas.create_rectangle(x, y, x + 122, y + 20, fill="#f7efe3", outline="")
        self.canvas.create_rectangle(x + 138, y, x + 260, y + 20, fill="#141414", outline="#50473e")
        self.canvas.create_text(x + 10, y + 10, text="White  " + self.clock_text(self.white_seconds), fill=INK, anchor="w", font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(x + 148, y + 10, text="Black  " + self.clock_text(self.black_seconds), fill="#f7efe3", anchor="w", font=("Segoe UI", 10, "bold"))

    def clock_text(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def draw_captured(self, x, y):
        self.canvas.create_text(x, y, text="Captured", fill="#f7efe3", anchor="w", font=("Segoe UI", 12, "bold"))
        white_lost = " ".join(UNICODE[p] for p in self.game.captured_pieces(WHITE)) or "-"
        black_lost = " ".join(UNICODE[p] for p in self.game.captured_pieces(BLACK)) or "-"
        score = self.game.material_score()
        lead = "Even" if score == 0 else ("White +" if score > 0 else "Black +") + str(abs(score) // 100)
        self.canvas.create_text(x, y + 24, text="W: " + white_lost, fill="#cabdae", anchor="w", font=("Segoe UI Symbol", 10), width=132)
        self.canvas.create_text(x, y + 45, text="B: " + black_lost, fill="#cabdae", anchor="w", font=("Segoe UI Symbol", 10), width=132)
        self.canvas.create_text(x, y + 66, text=lead, fill="#f7efe3", anchor="w", font=("Segoe UI", 9, "bold"))

    def draw_moves(self, x, y):
        self.canvas.create_text(x, y, text="Moves", fill="#f7efe3", anchor="w", font=("Segoe UI", 12, "bold"))
        recent = self.game.move_log[-4:]
        for idx in range(0, len(recent), 2):
            move_no = (len(self.game.move_log) - len(recent) + idx) // 2 + 1
            white = recent[idx]
            black = recent[idx + 1] if idx + 1 < len(recent) else ""
            self.canvas.create_text(x, y + 28 + (idx // 2) * 22, text=f"{move_no}. {white:<8} {black}", fill="#cabdae", anchor="w", font=("Consolas", 10))

    def draw_stats(self, x, y):
        text = f"Stats W{self.stats['white_wins']} B{self.stats['black_wins']} D{self.stats['draws']}"
        self.canvas.create_text(x, y + 9, text=text, fill="#9f9387", anchor="w", font=("Segoe UI", 9))

    def button(self, x, y, text, width=260):
        _, _, _, _, accent = self.theme()
        self.canvas.create_rectangle(x, y, x + width, y + 38, fill=accent, outline="#e5b958", width=2)
        self.canvas.create_text(x + width // 2, y + 19, text=text, fill=INK, font=("Segoe UI", 11, "bold"))

    def small_button(self, x, y, text, width=82, height=34):
        _, _, _, _, accent = self.theme()
        self.canvas.create_rectangle(x, y, x + width, y + height, fill=accent, outline="#e5b958", width=1)
        self.canvas.create_text(x + width // 2, y + height // 2, text=text, fill=INK, font=("Segoe UI", 9, "bold"), width=width - 4)

if __name__ == "__main__":
    root = tk.Tk()
    ChessUI(root)
    root.mainloop()