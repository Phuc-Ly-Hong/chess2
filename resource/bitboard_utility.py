import numpy as np

class BitboardUtility:
    FileA = 0x0101010101010101
    Rank1 = 0xFF
    Rank2 = Rank1 << 8
    Rank3 = Rank2 << 8
    Rank4 = Rank3 << 8
    Rank5 = Rank4 << 8
    Rank6 = Rank5 << 8
    Rank7 = Rank6 << 8
    Rank8 = Rank7 << 8

    notAFile = ~FileA & 0xFFFFFFFFFFFFFFFF
    notHFile = ~(FileA << 7) & 0xFFFFFFFFFFFFFFFF

    KnightAttacks = np.zeros(64, dtype=np.uint64)
    KingMoves = np.zeros(64, dtype=np.uint64)
    WhitePawnAttacks = np.zeros(64, dtype=np.uint64)
    BlackPawnAttacks = np.zeros(64, dtype=np.uint64)

    @staticmethod
    def pop_lsb(bitboard):
        if bitboard == 0:
            return -1, 0
        # Ép kiểu về int để dùng .bit_length()
        bb = int(bitboard)
        lsb_index = (bb & -bb).bit_length() - 1
        bitboard &= bitboard - 1
        return lsb_index, bitboard


    @staticmethod
    def set_square(bitboard, square):
        return bitboard | (1 << square)

    @staticmethod
    def clear_square(bitboard, square):
        return bitboard & ~(1 << square)

    @staticmethod
    def toggle_square(bitboard, square):
        return bitboard ^ (1 << square)

    @staticmethod
    def toggle_squares(bitboard, squareA, squareB):
        return bitboard ^ ((1 << squareA) | (1 << squareB))

    @staticmethod
    def contains_square(bitboard, square):
        return ((bitboard >> square) & 1) != 0

    @staticmethod
    def pawn_attacks(pawn_bitboard, is_white):
        if is_white:
            return ((pawn_bitboard << 9) & BitboardUtility.notAFile) | \
                   ((pawn_bitboard << 7) & BitboardUtility.notHFile)
        else:
            return ((pawn_bitboard >> 7) & BitboardUtility.notAFile) | \
                   ((pawn_bitboard >> 9) & BitboardUtility.notHFile)

    @staticmethod
    def shift(bitboard, shift):
        if shift > 0:
            return (bitboard << shift) & 0xFFFFFFFFFFFFFFFF
        else:
            return (bitboard >> -shift) & 0xFFFFFFFFFFFFFFFF

    @staticmethod
    def initialize():
        ortho_dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        diag_dirs = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        knight_moves = [(-2, -1), (-2, 1), (-1, 2), (1, 2),
                        (2, 1), (2, -1), (1, -2), (-1, -2)]

        for y in range(8):
            for x in range(8):
                square = y * 8 + x

                # King moves
                for dx, dy in ortho_dirs + diag_dirs:
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < 8 and 0 <= ty < 8:
                        target = ty * 8 + tx
                        BitboardUtility.KingMoves[square] |= 1 << target

                # Knight attacks
                for dx, dy in knight_moves:
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < 8 and 0 <= ty < 8:
                        target = ty * 8 + tx
                        BitboardUtility.KnightAttacks[square] |= 1 << target

                # Pawn attacks
                if x < 7 and y < 7:
                    BitboardUtility.WhitePawnAttacks[square] |= 1 << ((y + 1) * 8 + (x + 1))
                if x > 0 and y < 7:
                    BitboardUtility.WhitePawnAttacks[square] |= 1 << ((y + 1) * 8 + (x - 1))
                if x < 7 and y > 0:
                    BitboardUtility.BlackPawnAttacks[square] |= 1 << ((y - 1) * 8 + (x + 1))
                if x > 0 and y > 0:
                    BitboardUtility.BlackPawnAttacks[square] |= 1 << ((y - 1) * 8 + (x - 1))

    @staticmethod
    def lsb(bitboard):
        if bitboard == 0:
            return -1  # Không có bit nào bật
        return (int(bitboard) & -int(bitboard)).bit_length() - 1

# Initialize all precomputed tables
BitboardUtility.initialize()
