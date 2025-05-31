import numpy as np
from piece_square_table import PieceSquareTable
from precomputed_evaluation_data import OrthogonalDistance, CentreManhattanDistance ,PawnShieldSquaresWhite, PawnShieldSquaresBlack
from bitboard import Bits

PAWN_VALUE = 100
KNIGHT_VALUE = 300
BISHOP_VALUE = 320
ROOK_VALUE = 500
QUEEN_VALUE = 900

passed_pawn_bonuses = [0, 120, 80, 50, 30, 15, 15]
isolated_pawn_penalty_by_count = [0, -10, -25, -50, -75, -75, -75, -75, -75]
king_pawn_shield_scores = [4, 7, 4, 3, 6, 3]

endgame_material_start = ROOK_VALUE * 2 + BISHOP_VALUE + KNIGHT_VALUE

class EvaluationData:
    def __init__(self):
        self.material = 0
        self.pst = 0
        self.mopup = 0
        self.pawns = 0
        self.shield = 0

    def total(self):
        return self.material + self.pst + self.mopup + self.pawns + self.shield

class MaterialInfo:
    def __init__(self, board, color):
        self.pawns = board.count_pawns(color)
        self.knights = board.count_knights(color)
        self.bishops = board.count_bishops(color)
        self.rooks = board.count_rooks(color)
        self.queens = board.count_queens(color)

        self.material = (self.pawns * PAWN_VALUE + self.knights * KNIGHT_VALUE +
                         self.bishops * BISHOP_VALUE + self.rooks * ROOK_VALUE + self.queens * QUEEN_VALUE)

        self.enemy_pawns = board.get_pawn_bitboard(1 - color)
        self.own_pawns = board.get_pawn_bitboard(color)

        q, r, b, n = self.queens, self.rooks, self.bishops, self.knights
        endgame_start_weight = 2*20 + 2*10 + 2*10 + 45
        current = q*45 + r*20 + b*10 + n*10
        self.endgameT = 1 - min(1, current / endgame_start_weight)

class Evaluation:
    def __init__(self):
        self.board = None

    def evaluate(self, board):
        self.board = board
        white_eval = EvaluationData()
        black_eval = EvaluationData()

        white_material = MaterialInfo(board, 0)
        black_material = MaterialInfo(board, 1)

        white_eval.material = white_material.material
        black_eval.material = black_material.material

        white_eval.pst = self.evaluate_pst(0, white_material.endgameT)
        black_eval.pst = self.evaluate_pst(1, black_material.endgameT)

        white_eval.mopup = self.mopup_eval(True, white_material, black_material)
        black_eval.mopup = self.mopup_eval(False, black_material, white_material)

        white_eval.pawns = self.evaluate_pawns(0)
        black_eval.pawns = self.evaluate_pawns(1)

        white_eval.shield = self.king_pawn_shield(0, black_material, black_eval.pst)
        black_eval.shield = self.king_pawn_shield(1, white_material, white_eval.pst)

        total = (white_eval.total() - black_eval.total())
        return total if board.is_white_to_move() else -total

    def evaluate_pawns(self, color):
        pawns = self.board.get_pawn_bitboard(color)
        total = 0
        for sq in range(64):
            if ((pawns >> sq) & 1) == 0:
                continue

            file = sq % 8
            if (pawns & Bits.AdjacentFileMasks[file]) == 0:
                num = bin(pawns).count('1')
                total += isolated_pawn_penalty_by_count[num]

            forward = Bits.WhiteForwardFileMask[sq] if color == 0 else Bits.BlackForwardFileMask[sq]
            passed_mask = forward | Bits.AdjacentFileMasks[file]
            enemy_pawns = self.board.get_pawn_bitboard(1 - color)

            if (enemy_pawns & passed_mask) == 0:
                rank = sq // 8 if color == 0 else 7 - (sq // 8)
                total += passed_pawn_bonuses[rank]

        return total

    def evaluate_pst(self, color, endgameT):
        total = 0
        for piece_type in range(1, 6):
            pieces = self.board.get_piece_bitboard(color, piece_type)
            for sq in range(64):
                if ((pieces >> sq) & 1):
                    total += PieceSquareTable.read(piece_type, sq, color == 0)

        king_sq = self.board.king_square(color)
        if king_sq == -1:  
            return total   

        middle_score = PieceSquareTable.read(PieceSquareTable.KingStart, king_sq, color == 0)
        end_score = PieceSquareTable.read(PieceSquareTable.KingEnd, king_sq, color == 0)
        total += int((1 - endgameT) * middle_score + endgameT * end_score)
        return total

    def king_pawn_shield(self, color, enemy_material, base_score):
        if enemy_material.queens == 0:
            return 0

        score = 0
        king_sq = self.board.king_square(color)
        pawn_bb = self.board.get_pawn_bitboard(color)
        shields = PawnShieldSquaresWhite[king_sq] if color == 0 else PawnShieldSquaresBlack[king_sq]
        for i, s in enumerate(shields):
            if ((pawn_bb >> s) & 1):
                score += king_pawn_shield_scores[i % len(king_pawn_shield_scores)]
        return score

    def mopup_eval(self, is_white, my_mat, opp_mat):
        if my_mat.queens > 0 or opp_mat.material > endgame_material_start:
            return 0

        king_sq = self.board.king_square(0 if is_white else 1)
        opp_king_sq = self.board.king_square(1 if is_white else 0)
        bonus = OrthogonalDistance[opp_king_sq][king_sq] * 4
        bonus += (7 - CentreManhattanDistance[opp_king_sq]) * 10
        return bonus
