import numpy as np
from piece_square_table import PieceSquareTable
from precomputed_evaluation_data import OrthogonalDistance, CentreManhattanDistance ,PawnShieldSquaresWhite, PawnShieldSquaresBlack
from core.bitboard import Bits
from core.move_generator import MoveGenerator
from core.magic_bitboards import get_rook_attacks, get_bishop_attacks
from precomputed_move_data import PrecomputedMoveData
from core.bitboard_utility import BitboardUtility

PAWN_VALUE = 100
KNIGHT_VALUE = 300
BISHOP_VALUE = 320
ROOK_VALUE = 500
QUEEN_VALUE = 900

BISHOP_PAIR_BONUS = 50

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
        self.files = 0
        self.mobility = 0
        self.tropism = 0 
        self.center_control = 0
        self.piece_protection = 0

    def total(self):
        return (self.material + self.pst + self.mopup + self.pawns + self.shield + self.files + self.mobility+self.tropism+ self.center_control+self.piece_protection)

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

        white_eval.files = self.evaluate_open_files(0, white_material.endgameT)
        black_eval.files = self.evaluate_open_files(1, black_material.endgameT)

        white_eval.mobility = self.evaluate_mobility(0, white_material.endgameT)
        black_eval.mobility = self.evaluate_mobility(1, black_material.endgameT)

        white_eval.tropism = self.evaluate_king_tropism(0, white_material.endgameT)
        black_eval.tropism = self.evaluate_king_tropism(1, black_material.endgameT)

        white_eval.center_control = self.evaluate_center_control(0, white_material.endgameT)
        black_eval.center_control = self.evaluate_center_control(1, black_material.endgameT)

        white_eval.piece_protection = self.evaluate_piece_protection(0, white_material.endgameT)
        black_eval.piece_protection = self.evaluate_piece_protection(1, black_material.endgameT)

        # Bishop Pair Bonus
        if white_material.bishops >= 2:
            white_eval.material += BISHOP_PAIR_BONUS
        if black_material.bishops >= 2:
            black_eval.material += BISHOP_PAIR_BONUS

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
    
    def evaluate_open_files(self, color, endgameT):
        total = 0
        own_rooks = self.board.get_rooks(color)
        own_queens = self.board.get_queens(color)
        own_pawns = self.board.get_pawn_bitboard(color)
        enemy_pawns = self.board.get_pawn_bitboard(1 - color)

        
        for file in range(8):
            file_mask = Bits.FileMasks[file]
            
            # Kiểm tra cột mở (không có tốt của cả hai bên)
            if not (own_pawns | enemy_pawns) & file_mask:
                if own_rooks & file_mask:
                    total += 15 * (1 + endgameT * 0.5)  # Thưởng thêm trong tàn cuộc
                if own_queens & file_mask:
                    total += 10 * (1 - endgameT * 0.3)  # Giảm thưởng cho hậu trong tàn cuộc
            
            # Kiểm tra cột nửa mở (không có tốt của mình, có tốt của đối phương)
            elif not (own_pawns & file_mask) and (enemy_pawns & file_mask):
                if own_rooks & file_mask:
                    total += 10 * (1 + endgameT * 0.5)  # Thưởng cho xe trên cột nửa mở
                if own_queens & file_mask:
                    total += 5 * (1 - endgameT * 0.3)   # Thưởng ít hơn cho hậu

        return total

    def evaluate_mobility(self, color, endgameT):
        if self.board is None:
            return 0  # An toàn nếu board chưa được khởi tạo

        total = 0
        mobility_weights = {
            2: 4,   # Knight
            3: 3,   # Bishop
            4: 2,   # Rook
            5: 1    # Queen
        }

        # Lấy toàn bộ ô bị chiếm
        own_occ = self.board.get_occupied(color)
        enemy_occ = self.board.get_occupied(1 - color)
        occupied = own_occ | enemy_occ

        # Khởi tạo MoveGenerator để kiểm tra ghim
        move_gen = MoveGenerator()
        move_gen.board = self.board
        move_gen.init_state()  # init_state tự thiết lập các thuộc tính cần thiết
        move_gen.calculate_attack_data()

        if move_gen.friendly_king_square < 0:
            return 0  # An toàn nếu không tìm thấy vua

        for piece_type in range(2, 6):  # Knight to Queen
            pieces = self.board.get_piece_bitboard(color, piece_type)
            for sq in BitboardUtility.iter_bits(pieces):
                # Lấy các nước đi hợp lệ
                if piece_type == 2:  # Knight
                    attacks = BitboardUtility.KnightAttacks[sq]
                elif piece_type == 3:  # Bishop
                    attacks = get_bishop_attacks(sq, occupied)
                elif piece_type == 4:  # Rook
                    attacks = get_rook_attacks(sq, occupied)
                elif piece_type == 5:  # Queen
                    attacks = get_bishop_attacks(sq, occupied) | get_rook_attacks(sq, occupied)

                # Kiểm tra ghim
                if move_gen.is_pinned(sq):
                    attacks &= PrecomputedMoveData.alignMask[sq][move_gen.friendly_king_square]

                # Loại bỏ các ô bị quân mình chiếm
                legal_moves = attacks & (~own_occ & 0xFFFFFFFFFFFFFFFF)
                mobility = BitboardUtility.count_bits(legal_moves)

                # Áp dụng trọng số, điều chỉnh theo giai đoạn trận đấu
                weight = mobility_weights[piece_type] * (1 + endgameT * 0.2 if piece_type in [4, 5] else 1 - endgameT * 0.1)
                total += mobility * weight

        return total

    def evaluate_king_tropism(self, color, endgameT):
        if self.board is None:
            return 0  # An toàn nếu board chưa được khởi tạo

        tropism_bonus = 0
        opp_king_sq = self.board.king_square(1 - color)

        if opp_king_sq == -1:
            return 0  # Không có vua đối phương

        # Trọng số cho các loại quân (hậu, mã, xe, tượng)
        tropism_weights = {
            2: 2,   # Knight
            3: 1,   # Bishop
            4: 1.5, # Rook
            5: 4    # Queen
        }

        for piece_type in [2, 3, 4, 5]:  # Mã, tượng, xe, hậu
            pieces = self.board.get_piece_bitboard(color, piece_type)
            for sq in BitboardUtility.iter_bits(pieces):
                dist = OrthogonalDistance[sq][opp_king_sq]  # Dùng bảng tiền tính
                bonus = max(0, (7 - dist)) * tropism_weights[piece_type]
                tropism_bonus += bonus * (1 - endgameT * 0.5)  # Giảm ảnh hưởng trong tàn cuộc

        return tropism_bonus

    def evaluate_center_control(self, color, endgameT):
        if self.board is None:
            return 0  # An toàn nếu board chưa được khởi tạo

        # Định nghĩa các ô trung tâm và mở rộng bằng bitboard
        center_squares = 0x0000001818000000  # d4(27), e4(28), d5(35), e5(36)
        expanded_center = 0x00003C24243C0000  # c3(18), d3(19), e3(20), f3(21), c4(26), f4(29), c5(34), f5(37), c6(42), d6(43), e6(44), f6(45)

        # Trọng số cho từng loại quân
        center_weights = {1: 8, 2: 6, 3: 5, 4: 3, 5: 3}  # Tốt, mã, tượng, xe, hậu
        expanded_weights = {1: 4, 2: 3, 3: 2, 4: 1.5, 5: 1.5}

        bonus = 0

        # Khởi tạo MoveGenerator để kiểm tra ghim
        move_gen = MoveGenerator()
        move_gen.board = self.board
        move_gen.init_state()
        move_gen.calculate_attack_data()

        for piece_type in range(1, 6):  # Tốt, mã, tượng, xe, hậu
            pieces = self.board.get_piece_bitboard(color, piece_type)
            for sq in BitboardUtility.iter_bits(pieces):
                # Bỏ qua quân bị ghim
                if move_gen.is_pinned(sq):
                    continue
                # Kiểm tra ô trung tâm
                if (1 << sq) & center_squares:
                    bonus += center_weights[piece_type] * (1 - endgameT * 0.3)
                # Kiểm tra ô mở rộng
                elif (1 << sq) & expanded_center:
                    bonus += expanded_weights[piece_type] * (1 - endgameT * 0.3)

        return bonus

    def evaluate_piece_protection(self, color, endgameT):
        if self.board is None:
            return 0  # An toàn nếu board chưa được khởi tạo

        bonus = 0
        # Trọng số bảo vệ cho từng loại quân
        protection_weights = {1: 2, 2: 3, 3: 3, 4: 4, 5: 5}  # Tốt, mã, tượng, xe, hậu

        # Lấy các quân của mình
        own_occ = self.board.get_occupied(color)
        enemy_occ = self.board.get_occupied(1 - color)

        # Khởi tạo MoveGenerator để kiểm tra ghim
        move_gen = MoveGenerator()
        move_gen.board = self.board
        move_gen.init_state()
        move_gen.calculate_attack_data()

        # Duyệt qua từng loại quân trừ vua
        for pt in range(1, 6):  # Tốt (1) đến Hậu (5)
            pieces = self.board.get_piece_bitboard(color, pt)
            for sq in BitboardUtility.iter_bits(pieces):
                # Bỏ qua quân bị ghim
                if move_gen.is_pinned(sq):
                    continue
                # Lấy các quân bảo vệ (chỉ quân của mình)
                attackers = self.board.attackers_to(sq, color) & own_occ
                if attackers:
                    num_protectors = BitboardUtility.count_bits(attackers)
                    # Lấy các quân tấn công của đối phương
                    enemy_attackers = self.board.attackers_to(sq, 1 - color) & enemy_occ
                    num_enemy_attackers = BitboardUtility.count_bits(enemy_attackers)
                    # Tính điểm bảo vệ, trừ đi nếu bị tấn công nhiều hơn
                    protection_score = num_protectors - num_enemy_attackers
                    if protection_score > 0:
                        bonus += protection_score * protection_weights[pt] * (1 - 0.5 * endgameT)

        return bonus

