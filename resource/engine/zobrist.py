import random

class ZobristHasher:
    def __init__(self):
        self.piece_keys = {}
        self.castling_keys = {}
        self.en_passant_keys = [random.getrandbits(64) for _ in range(8)]
        self.side_key = random.getrandbits(64)
        self.init_random_keys()

    def init_random_keys(self):
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K']
        colors = ['w', 'b']
        for color in colors:
            for piece in pieces:
                for square in range(64):
                    self.piece_keys[(color + piece, square)] = random.getrandbits(64)

        for right in ['K', 'Q', 'k', 'q']:
            self.castling_keys[right] = random.getrandbits(64)

    def hash_board(self, board, side_to_move, castling_rights, en_passant_file):
        h = 0
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece:
                    square = (7 - rank) * 8 + file
                    h ^= self.piece_keys.get((piece, square), 0)

        for right in castling_rights:
            h ^= self.castling_keys.get(right, 0)

        if en_passant_file is not None:
            h ^= self.en_passant_keys[en_passant_file]

        if side_to_move == 'w':
            h ^= self.side_key

        return h
    
    def hash(self, board_wrapper):
        board = board_wrapper.board_array
        side_to_move = 'w' if board_wrapper.is_white_to_move() else 'b'
        castling_rights = board_wrapper.castling_rights

        # Tìm file bắt tốt qua đường nếu có
        ep_file = None
        move = board_wrapper.last_move

        if (
            isinstance(move, tuple) and len(move) == 2 and
            isinstance(move[0], tuple) and len(move[0]) == 2 and
            isinstance(move[1], tuple) and len(move[1]) == 2
        ):
            start, end = move
            sf, sr = start
            ef, er = end
            piece = board[sr][sf]
            if piece and piece[1] == 'P' and abs(sr - er) == 2:
                ep_file = sf
        else:
            # Bạn có thể bật dòng dưới để debug nếu cần
            # print(f"[Zobrist] Warning: Invalid last_move format: {move}")
            pass

        return self.hash_board(board, side_to_move, castling_rights, ep_file)


