import numpy as np
from core.bitboard_utility import BitboardUtility
from core.magic_bitboards import get_bishop_attacks, get_rook_attacks
import copy

class BoardWrapper:
    def __init__(self, board_array, castling_rights, turn, last_move):
        self.board_array = [row[:] for row in board_array]
        self.castling_rights = castling_rights
        self.turn = turn
        self.last_move = last_move
        self.en_passant_square = -1
        self._init_bitboards()

    def _init_bitboards(self):
        self.piece_bitboards = {
            'w': { 'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0, 'K': 0 },
            'b': { 'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0, 'K': 0 }
        }
        self.occupied = { 'w': 0, 'b': 0 }
        self.all_occupied = 0
        for rank in range(8):
            for file in range(8):
                sq = rank * 8 + file
                piece = self.board_array[rank][file]
                if piece:
                    color, p = piece[0], piece[1]
                    self.piece_bitboards[color][p] |= (1 << sq)
                    self.occupied[color] |= (1 << sq)
                    self.all_occupied |= (1 << sq)

    def get_pawn_bitboard(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['P']

    def get_knights(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['N']

    def get_bishops(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['B']

    def get_rooks(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['R']

    def get_queens(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['Q']

    def get_king(self, color):
        return self.piece_bitboards['w' if color == 0 else 'b']['K']

    def get_occupied(self, color):
        return self.occupied['w' if color == 0 else 'b']

    def get_all_occupied(self):
        return self.all_occupied

    def get_piece_bitboard(self, color, piece_type):
        piece_map = {1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K'}
        return self.piece_bitboards['w' if color == 0 else 'b'][piece_map[piece_type]]

    def king_square(self, color):
        king_bb = self.get_king(color)
        if king_bb == 0:
            return -1
        return BitboardUtility.lsb(king_bb)

    def is_white_to_move(self):
        return self.turn == 'w'

    def can_castle_kingside(self, is_white):
        return ('K' if is_white else 'k') in self.castling_rights

    def can_castle_queenside(self, is_white):
        return ('Q' if is_white else 'q') in self.castling_rights

    def count_pawns(self, color):
        return bin(self.get_pawn_bitboard(color)).count('1')

    def count_knights(self, color):
        return bin(self.get_knights(color)).count('1')

    def count_bishops(self, color):
        return bin(self.get_bishops(color)).count('1')

    def count_rooks(self, color):
        return bin(self.get_rooks(color)).count('1')

    def count_queens(self, color):
        return bin(self.get_queens(color)).count('1')

    def get_piece(self, square: int):
        if not isinstance(square, int):
            raise TypeError(f"[get_piece] square must be an integer, got {type(square)}: {square}")
        if not (0 <= square < 64):
            raise ValueError(f"[get_piece] Square index out of range: {square}")

        for color in ['w', 'b']:  
            for ptype in ['P', 'N', 'B', 'R', 'Q', 'K']:
                if (self.piece_bitboards[color][ptype] >> square) & 1:
                    return color + ptype

        return ""  # Ô trống

    def make_copy_and_apply(self, move):
        # Trường hợp đặc biệt: Null Move Pruning
        if move == ("null", "null"):
            new_board = [row[:] for row in self.board_array]
            wrapped = BoardWrapper(new_board, copy.deepcopy(self.castling_rights), 'b' if self.turn == 'w' else 'w', self.last_move)
            wrapped._init_bitboards()  # Đảm bảo bitboards được cập nhật
            return wrapped

        # Sao chép bảng hiện tại
        new_board = [row[:] for row in self.board_array]
        castling = copy.deepcopy(self.castling_rights)  # Sao chép sâu để tránh tham chiếu
        last = (move[0], move[1])

        start = move[0]
        target = move[1]
        promo = move[2] if len(move) > 2 else None

        # Xử lý nước đi đặc biệt (castling, en passant)
        if len(move) > 2 and move[2] == 'castle':
            # Xử lý castling (giả sử bạn có logic riêng cho castling)
            # Ví dụ: Di chuyển vua và xe, cập nhật castling_rights
            # Bạn cần thêm logic cụ thể ở đây
            pass
        elif len(move) > 2 and move[2] == 'ep':
            # Xử lý en passant
            # Ví dụ: Xóa quân tốt bị bắt, di chuyển tốt
            # Bạn cần thêm logic cụ thể ở đây
            pass

        # Lấy toạ độ hàng và cột từ ô xuất phát
        if isinstance(start, int):
            sf, sr = start % 8, start // 8
        else:
            sf, sr = start

        # Lấy toạ độ hàng và cột từ ô đích
        if isinstance(target, int):
            tf, tr = target % 8, target // 8
        else:
            tf, tr = target

        piece = new_board[sr][sf]

        # Kiểm tra quân cờ hợp lệ
        if not piece or not isinstance(piece, str) or len(piece) < 2:
            print(f"[ERROR] Invalid piece during move: '{piece}' at ({sr},{sf}) for move {move}")
            return self

        # Xoá quân ở ô đích nếu là quân địch (bắt quân)
        if new_board[tr][tf] and new_board[tr][tf][0] != piece[0]:
            new_board[tr][tf] = ""

        # Ghi quân mới vào ô đích
        if promo and promo in ['q', 'r', 'b', 'n']:
            new_board[tr][tf] = piece[0] + promo.upper()
        else:
            new_board[tr][tf] = piece

        # Xoá quân ở ô xuất phát
        new_board[sr][sf] = ""

        new_turn = 'b' if self.turn == 'w' else 'w'

        # Tạo đối tượng mới và cập nhật lại bitboards
        wrapped = BoardWrapper(new_board, castling, new_turn, last)
        print(f"[DEBUG] make_copy_and_apply(): self.turn = {self.turn}, new turn = {new_turn}")
        wrapped._init_bitboards()
        return wrapped

    def get_sliders(self, color, ortho=True):
        if ortho:
            return self.get_rooks(color) | self.get_queens(color)
        else:
            return self.get_bishops(color) | self.get_queens(color)

    def get_enemy_sliders(self, color, ortho=True):
        enemy_color = 'b' if color == 'w' else 'w'
        return self.get_sliders(enemy_color, ortho)

    def get_en_passant_square(self):
        return self.en_passant_square
    
    def get_all_pieces_of_color(self, color):
        """Return bitboard of all pieces of one color: 0 = white, 1 = black"""
        color_key = 'w' if color == 0 else 'b'
        result = 0
        for piece in self.piece_bitboards[color_key].values():
            result |= piece
        return result
    
    def move_gives_check(self, move):
        from core.move_generator import MoveGenerator
        applied_board = self.make_copy_and_apply(move)

        # Vì turn đã bị đảo sau khi đi nước đó → kẻ vừa bị chiếu là bên kia
        victim_color = 1 if applied_board.turn == 'w' else 0  # màu vua bị tấn công
        king_sq = applied_board.king_square(victim_color)

        if king_sq == -1:
            return False  # Không có vua - có thể là lỗi hoặc nước sai

        move_gen = MoveGenerator()
        move_gen.board = applied_board
        move_gen.init_state()
        move_gen.calculate_attack_data()

        is_attacked = move_gen.is_square_attacked(applied_board, king_sq, 'w' if victim_color == 0 else 'b')
        return is_attacked

    def does_move_block_check(self, move):
        from core.move_generator import MoveGenerator
        my_color = 0 if self.turn == 'w' else 1
        king_sq = self.king_square(my_color)
        if king_sq == -1:
            return False

        move_gen = MoveGenerator()
        if not move_gen.is_square_attacked(self, king_sq, 'b' if self.turn == 'w' else 'w'):
            return False  # Không bị chiếu thì không cần chặn

        # Áp dụng thử nước đi
        new_board = self.make_copy_and_apply(move)
        new_color = 0 if new_board.turn == 'w' else 1
        new_king_sq = new_board.king_square(new_color)

        if new_king_sq == -1:
            return False  # vua bị mất??

        # Nếu sau nước đi không còn bị chiếu nữa => đã chặn được chiếu
        return not move_gen.is_square_attacked(new_board, new_king_sq, 'b' if new_board.turn == 'w' else 'w')

    def is_capture(self, move):
        """
        Trả về True nếu nước đi là nước bắt quân (ô đích có quân đối phương).
        """
        from_sq, to_sq = move[0], move[1]
        target_piece = self.get_piece(to_sq)
        moving_piece = self.get_piece(from_sq)
        
        if not moving_piece:
            return False  # không có quân để di chuyển

        if target_piece and target_piece[0] != moving_piece[0]:
            return True  # có quân đối phương ở ô đích
        return False

    def attackers_to(self, sq, color):
        attackers = 0
        occupied = self.get_occupied(0) | self.get_occupied(1)

        # Tốt
        pawn_attacks = BitboardUtility.pawn_attacks(1 - color,sq)  # 1 - color vì tấn công từ góc nhìn của đối phương
        attackers |= pawn_attacks & self.get_piece_bitboard(color, 1)

        # Mã
        knight_attacks = BitboardUtility.KnightAttacks[sq]
        attackers |= knight_attacks & self.get_piece_bitboard(color, 2)

        # Tượng
        bishop_attacks = get_bishop_attacks(sq, occupied)
        attackers |= bishop_attacks & self.get_piece_bitboard(color, 3)

        # Xe
        rook_attacks = get_rook_attacks(sq, occupied)
        attackers |= rook_attacks & self.get_piece_bitboard(color, 4)

        # Hậu (kết hợp tượng và xe)
        queen_attacks = bishop_attacks | rook_attacks
        attackers |= queen_attacks & self.get_piece_bitboard(color, 5)

        return attackers



    





