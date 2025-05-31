import numpy as np
from bitboard_utility import BitboardUtility
import copy

class BoardWrapper:
    def __init__(self, board_array, castling_rights, turn, last_move):
        self.board_array = [row[:] for row in board_array]
        self.castling_rights = castling_rights
        self.turn = 'w' if turn else 'b'
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

    def get_piece(self, square):
        for color in ['w', 'b']:
            for p in ['P', 'N', 'B', 'R', 'Q', 'K']:
                if (self.piece_bitboards[color][p] >> square) & 1:
                    return f"{color}{p}"
        return None

    def make_copy_and_apply(self, move):
        # Sao chép bảng hiện tại
        new_board = [row[:] for row in self.board_array]
        castling = self.castling_rights
        last = (move[0], move[1])
        turn = self.turn == 'w'

        start = move[0]
        target = move[1]
        promo = move[2] if len(move) > 2 else None

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

        # Nếu không có quân cờ hợp lệ tại ô xuất phát
        if not piece or len(piece) < 2:
            print(f"[ERROR] Invalid piece during move: '{piece}' at ({sr},{sf}) for move {move}")
            return self

        # Xoá quân ở ô đích nếu là quân địch (bắt quân)
        if new_board[tr][tf] and new_board[tr][tf][0] != piece[0]:
            new_board[tr][tf] = ""

        # Ghi quân mới vào ô đích
        if promo:
            new_board[tr][tf] = piece[0] + promo.upper()
        else:
            new_board[tr][tf] = piece

        # Xoá quân ở ô xuất phát
        new_board[sr][sf] = ""

        # Tạo đối tượng mới và cập nhật lại bitboards
        wrapped = BoardWrapper(new_board, castling, not turn, last)
        wrapped._init_bitboards()  # Cập nhật lại bitboards sau khi thực hiện nước đi
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
        from move_generator import MoveGenerator
        """Kiểm tra nếu move này có tạo ra chiếu sau khi đi."""
        applied_board = self.make_copy_and_apply(move)
        enemy_color = 1 if self.turn == 'w' else 0  # đổi lượt
        king_sq = applied_board.king_square(enemy_color)

        if king_sq == -1:
            return False  # Không tìm thấy vua

        move_gen = MoveGenerator()
        attacked = move_gen.is_square_attacked(applied_board, king_sq, 'w' if enemy_color == 0 else 'b')
        return attacked
    
    def does_move_block_check(self, move):
        from move_generator import MoveGenerator
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



    





