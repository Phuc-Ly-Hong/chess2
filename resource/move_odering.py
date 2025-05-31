import numpy as np
from collections import defaultdict
from bitboard_utility import BitboardUtility
from move_generator import MoveGenerator

class MoveOrdering:
    def __init__(self):
        self.killer_moves = defaultdict(list)
        self.history_heuristic = defaultdict(int)
        self.counter_moves = defaultdict(lambda: defaultdict(int))
        self.board = None

    def score_move(self, move, depth, pv_move=None, tt_move=None):
        start, target = move[0], move[1]
        promotion = move[2] if len(move) > 2 else None

        if move == pv_move:
            return 10_000_000  # Ưu tiên tuyệt đối
        if move == tt_move:
            return 9_000_000

        score = 0

        if promotion:
            score += 8_000_000 + self.promotion_bonus(promotion)

        score += self.estimate_move_value(self.board, move)

        if self.is_defensive(move):
            score += 2_000_000

        if self.board and self.board.move_gives_check(move):
            score += 1_000_000

        if self.is_king_move(move):
            score -= 1_000_000

        if move in self.killer_moves[depth]:
            score += 500_000

        score += self.history_heuristic[(start, target)]
        score += self.counter_moves[start][target] * 10

        if depth >= 6:
            piece = self.board.get_piece(move[0])
            target = move[1]
            if piece and piece[1] in ['N', 'B']:
                if target in [16, 18, 20, 22, 40, 42, 44, 46]:
                    score += 300
            if piece and piece[1] == 'P':
                if target in [27, 28, 35, 36]:
                    score += 200

        return score

    def promotion_bonus(self, promo):
        return {'q': 400, 'r': 300, 'b': 200, 'n': 100}.get(promo, 0)

    def add_killer(self, depth, move):
        if not self.board.is_capture(move):
            if move not in self.killer_moves[depth]:
                self.killer_moves[depth].insert(0, move)
                if len(self.killer_moves[depth]) > 2:
                    self.killer_moves[depth].pop()

    def add_history(self, move, depth):
        key = (move[0], move[1])
        self.history_heuristic[key] = min(self.history_heuristic[key] + depth * depth, 2_000_000)

    def update_killers_and_history(self, move, depth, is_cutoff):
        if is_cutoff and not self.board.is_capture(move):
            self.add_killer(depth, move)
        self.add_history(move, depth)

    def add_counter_move(self, last_move, current_move):
        if last_move and len(last_move) >= 2 and len(current_move) >= 2:
            last_piece = self.board.get_piece(last_move[1])
            current_piece = self.board.get_piece(current_move[0])
            if last_piece and current_piece:
                if abs(last_move[1] - current_move[0]) <= 2:
                    from_sq = last_move[1]
                    to_sq = current_move[1]
                    self.counter_moves[from_sq][to_sq] += 1
                    self.counter_moves[from_sq][to_sq] = min(self.counter_moves[from_sq][to_sq], 500)

    def order_moves(self, moves, depth, board=None, pv_move=None, tt_move=None):
        if not moves:
            return moves

        if board:
            self.board = board

        captures = []
        checks = []
        quiet = []
        castling = []

        for move in moves:
            if move == pv_move or move == tt_move:
                continue
            if board.is_capture(move):
                captures.append(move)
            elif board.move_gives_check(move):
                checks.append(move)
            elif len(move) > 2 and move[2] == 'castle':
                castling.append(move)
            else:
                quiet.append(move)

        scored_captures = [(self.estimate_move_value(board, m), m) for m in captures]
        scored_captures.sort(reverse=True)

        scored_checks = [(1000 if board.get_piece(m[0])[1] == 'N' else 500, m) for m in checks]
        scored_checks.sort(reverse=True)

        scored_quiet = [(self.history_heuristic[(m[0], m[1])], m) for m in quiet]
        scored_quiet.sort(reverse=True)

        ordered_moves = []
        if pv_move:
            ordered_moves.append(pv_move)
        if tt_move and tt_move != pv_move:
            ordered_moves.append(tt_move)
        ordered_moves.extend([m for (_, m) in scored_captures])
        ordered_moves.extend([m for (_, m) in scored_checks])
        ordered_moves.extend([m for (_, m) in scored_quiet])
        ordered_moves.extend(castling)

        return ordered_moves

    def estimate_move_value(self, board, move):
        from_sq, to_sq = move[0], move[1]
        attacker = board.get_piece(from_sq)
        victim = board.get_piece(to_sq)

        piece_values = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 950, 'K': 0,
            'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 950, 'k': 0,
        }

        if not victim:
            enemy_king_sq = board.king_square(1 if board.turn == 'w' else 0)
            if enemy_king_sq != -1:
                distance = abs(to_sq % 8 - enemy_king_sq % 8) + abs(to_sq // 8 - enemy_king_sq // 8)
                return max(0, 50 - distance * 5)
            return 0

        victim_value = piece_values.get(victim[1], 0)
        attacker_value = piece_values.get(attacker[1], 1) if attacker else 1

        bonus = 0
        if len(move) > 2 and move[2] == 'ep':
            bonus += 100
        elif len(move) > 2 and move[2] in ['q', 'r', 'b', 'n']:
            bonus += 200 if move[2] == 'q' else 100

        base_score = victim_value * 10 - attacker_value + bonus
        see_score = self.see(board, to_sq, from_sq)

        if see_score > 0:
            return base_score + see_score * 50
        return base_score - abs(see_score) * 30

    def is_defensive(self, move):
        if not self.board:
            return False

        king_sq = self.board.king_square(0 if self.board.turn == 'w' else 1)
        if king_sq == -1:
            return False

        in_check = self.board.is_square_attacked(king_sq, 'b' if self.board.turn == 'w' else 'w')
        if not in_check:
            return False

        from_sq = move[0]
        piece = self.board.get_piece(from_sq)
        if piece and piece[1] == 'K':
            return True

        return self.board.does_move_block_check(move)

    def is_king_move(self, move):
        if not self.board:
            return False
        piece = self.board.get_piece(move[0])
        return piece and piece[1] == 'K'

    def see(self, board, to_sq, from_sq, depth_limit=5):
        # Simplified SEE to prevent recursion loops
        piece = board.get_piece(from_sq)
        if not piece:
            return 0

        value = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 950, 'K': 20000,
            'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 950, 'k': 20000,
        }

        attacker_value = value.get(piece[1], 0)
        target_piece = board.get_piece(to_sq)
        victim_value = value.get(target_piece[1], 0) if target_piece else 0

        return victim_value - attacker_value