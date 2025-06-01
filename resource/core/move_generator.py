from bitboard_utility import BitboardUtility
from bitboard import Bits
from magic_bitboards import get_rook_attacks, get_bishop_attacks, get_slider_attacks
from engine.precomputed_move_data import PrecomputedMoveData
from board_wrapper import BoardWrapper

class MoveGenerator:
    MaxMoves = 218

    class PromotionMode:
        All = 0
        QueenOnly = 1
        QueenAndKnight = 2

    def __init__(self):
        self.promotions_to_generate = self.PromotionMode.All
        self.curr_move_index = 0
        self.moves = []
        self.generate_quiet_moves = True

    def generate_moves(self, board, captures_only=False):
        print(f"[DEBUG] Bat dau generate_moves(captures_only={captures_only})")
        self.board = board
        self.moves.clear()
        self.generate_quiet_moves = not captures_only
        self.is_white_to_move = board.turn == 'w'
        self.friendly_colour = 'w' if self.is_white_to_move else 'b'
        self.opponent_colour = 'b' if self.is_white_to_move else 'w'

        self.all_pieces = board.get_all_occupied()
        self.enemy_pieces = board.get_occupied(self.opponent_colour)
        self.friendly_pieces = board.get_occupied(self.friendly_colour)
        self.empty_squares = ~self.all_pieces & 0xFFFFFFFFFFFFFFFF

        print("[DEBUG] Goi init_state()")
        self.init_state()
        print("[DEBUG] Goi generate_king_moves()")
        self.generate_king_moves()
        print("[DEBUG] Goi generate_sliding_moves()")
        self.generate_sliding_moves()
        print("[DEBUG] Goi generate_knight_moves()")
        self.generate_knight_moves()
        print("[DEBUG] Goi generate_pawn_moves()")
        self.generate_pawn_moves()

        # ✅ Lọc nước đi không khiến vua bị chiếu
        legal_moves = []
        friendly_color = self.friendly_colour
        opponent_color = self.opponent_colour

        print(f"[DEBUG] Tong so nuoc sinh ra truoc loc: {len(self.moves)}")

        for move in self.moves:
            new_board = board.make_copy_and_apply(move)
            print(f"[DEBUG] generate_moves(): turn = {board.turn}")
            king_sq = new_board.king_square(0 if friendly_color == 'w' else 1)

            if king_sq == -1:
                continue  # Không có vua → bỏ

            if not self.is_square_attacked_simple(new_board, king_sq, opponent_color):
                legal_moves.append(move)

        print(f"[DEBUG] So nuoc hop le sau loc: {len(legal_moves)}")
        print("[DEBUG] Ket thuc generate_moves()")
        return legal_moves

    def init_state(self):
        self.in_check = False
        self.in_double_check = False
        self.check_ray_bitmask = 0
        self.pin_rays = 0

        self.is_white_to_move = self.board.turn == 'w'
        self.friendly_colour = 'w' if self.is_white_to_move else 'b'
        self.opponent_colour = 'b' if self.is_white_to_move else 'w'

        color_int = 0 if self.friendly_colour == 'w' else 1
        self.friendly_king_square = self.board.king_square(color_int)


        self.enemy_pieces = self.board.get_occupied(self.opponent_colour)
        self.friendly_pieces = self.board.get_occupied(self.friendly_colour)
        self.all_pieces = self.board.get_all_occupied()
        self.empty_squares = ~self.all_pieces & 0xFFFFFFFFFFFFFFFF
        self.empty_or_enemy_squares = self.empty_squares | self.enemy_pieces
        self.move_type_mask = self.enemy_pieces if not self.generate_quiet_moves else 0xFFFFFFFFFFFFFFFF
        print(f"[DEBUG] Vua ben minh nam o o: {self.friendly_king_square}")
        print("[DEBUG] Before calculate_attack_data")

        self.calculate_attack_data()
        print("[DEBUG] After calculate_attack_data")

    def in_check_state(self):
        return self.in_check
    
    def is_square_attacked(self, board, square, attacker_color):
        attackers = 0
        color_int = 0 if attacker_color == 'w' else 1
        # Knight attacks
        attackers |= BitboardUtility.KnightAttacks[square] & board.get_knights(color_int)
        # Pawn attacks
        attackers |= BitboardUtility.pawn_attacks(1 << square, attacker_color == 'w') & board.get_pawn_bitboard(color_int)
        # King attacks
        attackers |= BitboardUtility.KingMoves[square] & board.get_king(color_int)
        # Sliding attacks
        attackers |= get_rook_attacks(square, board.get_all_occupied()) & (board.get_rooks(color_int) | board.get_queens(color_int))
        attackers |= get_bishop_attacks(square, board.get_all_occupied()) & (board.get_bishops(color_int) | board.get_queens(color_int))
        return attackers != 0

    def generate_king_moves(self):
        legal_mask = ~(self.opponent_attack_map | self.friendly_pieces)
        king_moves = BitboardUtility.KingMoves[self.friendly_king_square] & legal_mask & self.move_type_mask

        while king_moves:
            target, king_moves = BitboardUtility.pop_lsb(king_moves)
            self.moves.append((self.friendly_king_square, target))

        if not self.in_check and self.generate_quiet_moves:
            blockers = self.opponent_attack_map | self.all_pieces
            if self.board.can_castle_kingside(self.is_white_to_move):
                mask = Bits.WhiteKingsideMask if self.is_white_to_move else Bits.BlackKingsideMask
                if (mask & blockers) == 0:
                    target = 6 if self.is_white_to_move else 62
                    self.moves.append((self.friendly_king_square, target, 'castle'))
            if self.board.can_castle_queenside(self.is_white_to_move):
                mask2 = Bits.WhiteQueensideMask2 if self.is_white_to_move else Bits.BlackQueensideMask2
                full_mask = Bits.WhiteQueensideMask if self.is_white_to_move else Bits.BlackQueensideMask
                if (mask2 & blockers) == 0 and (full_mask & self.all_pieces) == 0:
                    target = 2 if self.is_white_to_move else 58
                    self.moves.append((self.friendly_king_square, target, 'castle'))

    def generate_sliding_moves(self):
        move_mask = self.empty_or_enemy_squares & self.check_ray_bitmask & self.move_type_mask
        ortho_sliders = self.board.get_sliders(self.friendly_colour, ortho=True)
        diag_sliders = self.board.get_sliders(self.friendly_colour, ortho=False)

        for start_square in BitboardUtility.iter_bits(ortho_sliders):
            moves = get_rook_attacks(start_square, self.all_pieces) & move_mask
            if self.is_pinned(start_square):
                moves &= PrecomputedMoveData.alignMask[start_square][self.friendly_king_square]
            for target in BitboardUtility.iter_bits(moves):
                self.moves.append((start_square, target))

        for start_square in BitboardUtility.iter_bits(diag_sliders):
            moves = get_bishop_attacks(start_square, self.all_pieces) & move_mask
            if self.is_pinned(start_square):
                moves &= PrecomputedMoveData.alignMask[start_square][self.friendly_king_square]
            for target in BitboardUtility.iter_bits(moves):
                self.moves.append((start_square, target))

    def generate_knight_moves(self):
        knights = self.board.get_knights(self.friendly_colour) & ~self.pin_rays
        move_mask = self.empty_or_enemy_squares & self.check_ray_bitmask & self.move_type_mask

        for start_square in BitboardUtility.iter_bits(knights):
            attacks = BitboardUtility.KnightAttacks[start_square] & move_mask
            for target_square in BitboardUtility.iter_bits(attacks):
                self.moves.append((start_square, target_square))

    def generate_pawn_moves(self):
        color_int = 0 if self.friendly_colour == 'w' else 1
        pawns = self.board.get_pawn_bitboard(color_int)
        push_dir = -8 if self.is_white_to_move else 8
        promo_rank = 0 if self.is_white_to_move else 7
        start_rank = 6 if self.is_white_to_move else 1

        for square in BitboardUtility.iter_bits(pawns):
            rank = square // 8
            file = square % 8

            # Đi 1 bước nếu không bị chặn và generate_quiet_moves bật
            one_forward = square + push_dir
            if self.generate_quiet_moves and 0 <= one_forward < 64 and not BitboardUtility.contains_square(self.all_pieces, one_forward):
                if one_forward // 8 == promo_rank:
                    self.add_promotion(square, one_forward)
                else:
                    self.moves.append((square, one_forward))
                    # Đi 2 bước nếu ở hàng xuất phát
                    if rank == start_rank:
                        two_forward = square + push_dir * 2
                        if 0 <= two_forward < 64 and not BitboardUtility.contains_square(self.all_pieces, two_forward):
                            self.moves.append((square, two_forward, 'pawn2up'))

            # Bắt chéo trái/phải
            for dx in [-1, 1]:
                nx = file + dx
                if 0 <= nx < 8:
                    target = square + push_dir + dx
                    if 0 <= target < 64 and BitboardUtility.contains_square(self.enemy_pieces, target):
                        if target // 8 == promo_rank:
                            self.add_promotion(square, target)
                        else:
                            self.moves.append((square, target))

        # Bắt tốt qua đường
        ep_square = self.board.get_en_passant_square()
        if ep_square != -1:
            for dx in [-1, 1]:
                capture_square = ep_square - push_dir
                attacker = ep_square + dx - push_dir
                if 0 <= attacker < 64 and BitboardUtility.contains_square(pawns, attacker):
                    if not self.in_check_after_en_passant(attacker, ep_square, capture_square):
                        self.moves.append((attacker, ep_square, 'ep'))

    def add_promotion(self, start, target):
        self.moves.append((start, target, 'q'))
        if self.generate_quiet_moves:
            if self.promotions_to_generate == self.PromotionMode.All:
                self.moves.append((start, target, 'n'))
                self.moves.append((start, target, 'r'))
                self.moves.append((start, target, 'b'))
            elif self.promotions_to_generate == self.PromotionMode.QueenAndKnight:
                self.moves.append((start, target, 'n'))

    def in_check_after_en_passant(self, start, target, captured):
        enemy_rooks = self.board.get_enemy_sliders(self.friendly_colour, ortho=True)
        if enemy_rooks:
            blockers = self.all_pieces ^ ((1 << start) | (1 << captured))
            rook_attacks = get_rook_attacks(self.friendly_king_square, blockers)
            return (rook_attacks & enemy_rooks) != 0
        return False
    
    def get_attackers(self, board, square, occupied_mask):
        attackers = 0
        for color in [0, 1]:
            # Knights
            attackers |= BitboardUtility.KnightAttacks[square] & board.get_knights(color)
            # Pawns
            attackers |= BitboardUtility.pawn_attacks(1 << square, color == 0) & board.get_pawn_bitboard(color)
            # Kings
            attackers |= BitboardUtility.KingMoves[square] & board.get_king(color)
            # Sliders
            attackers |= get_rook_attacks(square, occupied_mask) & (board.get_rooks(color) | board.get_queens(color))
            attackers |= get_bishop_attacks(square, occupied_mask) & (board.get_bishops(color) | board.get_queens(color))
        return attackers
    
    def is_king_in_check(self, board: BoardWrapper, color: str) -> bool:
        king_sq = board.king_square(0 if color == 'w' else 1)
        if king_sq == -1:
            return True
        return self.is_square_attacked(board, king_sq, 'b' if color == 'w' else 'w')

    def calculate_attack_data(self):
        king_sq = self.friendly_king_square
        self.opponent_attack_map = 0
        opponent_king_sq = self.board.king_square(0 if self.opponent_colour == 'w' else 1)
        if opponent_king_sq != -1:
            self.opponent_attack_map |= BitboardUtility.KingMoves[opponent_king_sq]

        # Knight checks
        knights = self.board.get_knights(self.opponent_colour)
        while knights:
            sq, knights = BitboardUtility.pop_lsb(knights)
            self.opponent_attack_map |= BitboardUtility.KnightAttacks[sq]
            if 0 <= sq < 64 and BitboardUtility.KnightAttacks[sq] is not None and BitboardUtility.contains_square(BitboardUtility.KnightAttacks[sq], king_sq):
                self.in_double_check = self.in_check
                self.in_check = True
                self.check_ray_bitmask |= 1 << sq

        # Pawn attacks
        pawns = self.board.get_pawn_bitboard(1 if self.opponent_colour == 'b' else 0)
        pawn_attacks = BitboardUtility.pawn_attacks(pawns, self.opponent_colour == 'w')
        self.opponent_attack_map |= pawn_attacks
        if BitboardUtility.contains_square(pawn_attacks, king_sq):
            self.in_double_check = self.in_check
            self.in_check = True
            white = self.opponent_colour == 'w'
            attacker_mask = BitboardUtility.WhitePawnAttacks[king_sq] if white else BitboardUtility.BlackPawnAttacks[king_sq]
            attackers = pawns & attacker_mask
            self.check_ray_bitmask |= attackers

        # Sliding pieces
        for dir_idx, offset in enumerate(PrecomputedMoveData.directionOffsets):
            ray_mask = 0
            blocked = False
            pinned_piece_sq = -1

            for i in range(1, PrecomputedMoveData.numSquaresToEdge[king_sq][dir_idx] + 1):
                sq = king_sq + offset * i
                piece = self.board.get_piece(sq)
                ray_mask |= 1 << sq

                if piece is None:
                    continue
                if not piece or len(piece) < 2:
                    continue  

                piece_color, piece_type = piece[0], piece[1]

                if piece_color == self.friendly_colour:
                    if pinned_piece_sq == -1:
                        pinned_piece_sq = sq  # Possible pinned piece
                    else:
                        break  # Multiple friendly pieces block the ray

                elif piece_color == self.opponent_colour:
                    if ((dir_idx < 4 and piece_type in ['R', 'Q']) or
                        (dir_idx >= 4 and piece_type in ['B', 'Q'])):

                        if pinned_piece_sq != -1:
                            self.pin_rays |= ray_mask
                        else:
                            # If piece is checking the king
                            if i == 1:
                                self.in_double_check = self.in_check
                                self.in_check = True
                            self.check_ray_bitmask |= ray_mask
                        break
                    else:
                        break

        self.not_pin_rays = ~self.pin_rays & 0xFFFFFFFFFFFFFFFF

    def is_square_attacked_simple(self, board, square, attacker_color):
        """Kiểm tra nhanh không sử dụng cache, dùng để validate moves"""
        if square < 0 or square >= 64:
            return False
        
        color_int = 0 if attacker_color == 'w' else 1
        occupied = board.get_all_occupied()
        
        # Knight attacks (8 hướng hình chữ L)
        if BitboardUtility.KnightAttacks[square] & board.get_knights(color_int):
            return True
            
        # Pawn attacks (phải xác định đúng hướng tấn công)
        if attacker_color == 'w':
            # Tốt trắng tấn công từ dưới lên (2 hướng chéo)
            pawn_attacks = (BitboardUtility.WhitePawnAttacks[square] & 
                            board.get_pawn_bitboard(color_int))
        else:
            # Tốt đen tấn công từ trên xuống (2 hướng chéo)
            pawn_attacks = (BitboardUtility.BlackPawnAttacks[square] & 
                            board.get_pawn_bitboard(color_int))
        
        if pawn_attacks:
            return True
            
        # Rook/Queen attacks (dọc + ngang)
        rook_queen = board.get_rooks(color_int) | board.get_queens(color_int)
        if get_rook_attacks(square, occupied) & rook_queen:
            return True
            
        # Bishop/Queen attacks (chéo)
        bishop_queen = board.get_bishops(color_int) | board.get_queens(color_int)
        if get_bishop_attacks(square, occupied) & bishop_queen:
            return True
            
        return False

    def is_pinned(self, square):
        return (self.pin_rays >> square) & 1

# Helper method: iterator over set bits
setattr(BitboardUtility, "iter_bits", staticmethod(lambda bb: (i for i in range(64) if ((bb >> i) & 1))))