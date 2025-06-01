import numpy as np
from bitboard_utility import BitboardUtility

class Bits:
    FileMasks = [
        0x0101010101010101,  # Cột A
        0x0202020202020202,  # Cột B
        0x0404040404040404,  # Cột C
        0x0808080808080808,  # Cột D
        0x1010101010101010,  # Cột E
        0x2020202020202020,  # Cột F
        0x4040404040404040,  # Cột G
        0x8080808080808080   # Cột H
    ]
    WhiteKingsideMask = (1 << 5) | (1 << 6)
    BlackKingsideMask = (1 << 61) | (1 << 62)

    WhiteQueensideMask2 = (1 << 3) | (1 << 2)
    BlackQueensideMask2 = (1 << 59) | (1 << 58)

    WhiteQueensideMask = WhiteQueensideMask2 | (1 << 1)
    BlackQueensideMask = BlackQueensideMask2 | (1 << 57)

    WhitePassedPawnMask = np.zeros(64, dtype=np.uint64)
    BlackPassedPawnMask = np.zeros(64, dtype=np.uint64)
    WhitePawnSupportMask = np.zeros(64, dtype=np.uint64)
    BlackPawnSupportMask = np.zeros(64, dtype=np.uint64)
    FileMask = np.zeros(8, dtype=np.uint64)
    AdjacentFileMasks = np.zeros(8, dtype=np.uint64)
    KingSafetyMask = np.zeros(64, dtype=np.uint64)
    WhiteForwardFileMask = np.zeros(64, dtype=np.uint64)
    BlackForwardFileMask = np.zeros(64, dtype=np.uint64)
    TripleFileMask = np.zeros(8, dtype=np.uint64)

    @staticmethod
    def init():
        for i in range(8):
            Bits.FileMask[i] = Bits.FileMasks[0] << i
            left = Bits.FileMasks[0] << (i - 1) if i > 0 else 0
            right = Bits.FileMasks[0] << (i + 1) if i < 7 else 0
            Bits.AdjacentFileMasks[i] = left | right

        for i in range(8):
            clamped = max(1, min(6, i))
            Bits.TripleFileMask[i] = Bits.FileMask[clamped] | Bits.AdjacentFileMasks[clamped]

        for square in range(64):
            file = square % 8
            rank = square // 8

            adjacent_files = (Bits.FileMasks[0] << max(0, file - 1)) | (Bits.FileMasks[0] << min(7, file + 1))
            white_forward_mask = ~((1 << (8 * (rank + 1))) - 1) & 0xFFFFFFFFFFFFFFFF
            black_forward_mask = ((1 << (8 * rank)) - 1)

            Bits.WhitePassedPawnMask[square] = (Bits.FileMask[file] | adjacent_files) & white_forward_mask
            Bits.BlackPassedPawnMask[square] = (Bits.FileMask[file] | adjacent_files) & black_forward_mask

            adjacent = 0
            if file > 0:
                adjacent |= 1 << (square - 1)
            if file < 7:
                adjacent |= 1 << (square + 1)

            Bits.WhitePawnSupportMask[square] = adjacent | BitboardUtility.shift(adjacent, -8)
            Bits.BlackPawnSupportMask[square] = adjacent | BitboardUtility.shift(adjacent, 8)

            Bits.WhiteForwardFileMask[square] = white_forward_mask & Bits.FileMask[file]
            Bits.BlackForwardFileMask[square] = black_forward_mask & Bits.FileMask[file]

        for i in range(64):
            Bits.KingSafetyMask[i] = BitboardUtility.KingMoves[i] | (1 << i)
Bits.init()
