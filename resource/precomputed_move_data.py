import numpy as np

class PrecomputedMoveData:
    directionOffsets = [8, -8, -1, 1, 7, -7, 9, -9]  # N, S, W, E, NW, SE, NE, SW

    numSquaresToEdge = np.zeros((64, 8), dtype=np.int8)
    knightMoves = [[] for _ in range(64)]
    kingMoves = [[] for _ in range(64)]
    pawnAttackDirections = [[4, 6], [7, 5]]  # White, Black
    pawnAttacksWhite = [[] for _ in range(64)]
    pawnAttacksBlack = [[] for _ in range(64)]
    directionLookup = np.zeros(127, dtype=np.int8)
    kingAttackBitboards = np.zeros(64, dtype=np.uint64)
    knightAttackBitboards = np.zeros(64, dtype=np.uint64)
    pawnAttackBitboards = [[0, 0] for _ in range(64)]
    rookMoves = np.zeros(64, dtype=np.uint64)
    bishopMoves = np.zeros(64, dtype=np.uint64)
    queenMoves = np.zeros(64, dtype=np.uint64)
    OrthogonalDistance = np.zeros((64, 64), dtype=np.int8)
    kingDistance = np.zeros((64, 64), dtype=np.int8)
    CentreManhattanDistance = np.zeros(64, dtype=np.int8)
    alignMask = np.zeros((64, 64), dtype=np.uint64)
    dirRayMask = np.zeros((8, 64), dtype=np.uint64)

    @staticmethod
    def is_valid(x, y):
        return 0 <= x < 8 and 0 <= y < 8

    @staticmethod
    def index(x, y):
        return y * 8 + x

    @staticmethod
    def coord(index):
        return index % 8, index // 8

    @staticmethod
    def initialize():
        # Num squares to edge
        for square in range(64):
            x, y = PrecomputedMoveData.coord(square)
            PrecomputedMoveData.numSquaresToEdge[square][0] = 7 - y  # N
            PrecomputedMoveData.numSquaresToEdge[square][1] = y      # S
            PrecomputedMoveData.numSquaresToEdge[square][2] = x      # W
            PrecomputedMoveData.numSquaresToEdge[square][3] = 7 - x  # E
            PrecomputedMoveData.numSquaresToEdge[square][4] = min(7 - y, x)      # NW
            PrecomputedMoveData.numSquaresToEdge[square][5] = min(y, 7 - x)      # SE
            PrecomputedMoveData.numSquaresToEdge[square][6] = min(7 - y, 7 - x)  # NE
            PrecomputedMoveData.numSquaresToEdge[square][7] = min(y, x)          # SW

        # Knight moves
        knight_deltas = [(-2, -1), (-2, 1), (-1, 2), (1, 2),
                         (2, 1), (2, -1), (1, -2), (-1, -2)]
        for square in range(64):
            x, y = PrecomputedMoveData.coord(square)
            bitboard = 0
            for dx, dy in knight_deltas:
                nx, ny = x + dx, y + dy
                if PrecomputedMoveData.is_valid(nx, ny):
                    idx = PrecomputedMoveData.index(nx, ny)
                    PrecomputedMoveData.knightMoves[square].append(idx)
                    bitboard |= 1 << idx
            PrecomputedMoveData.knightAttackBitboards[square] = bitboard

        # King moves
        for square in range(64):
            x, y = PrecomputedMoveData.coord(square)
            bitboard = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if PrecomputedMoveData.is_valid(nx, ny):
                        idx = PrecomputedMoveData.index(nx, ny)
                        PrecomputedMoveData.kingMoves[square].append(idx)
                        bitboard |= 1 << idx
            PrecomputedMoveData.kingAttackBitboards[square] = bitboard

        # Pawn attacks
        for square in range(64):
            x, y = PrecomputedMoveData.coord(square)
            for dx in [-1, 1]:
                if y < 7:
                    idx = PrecomputedMoveData.index(x + dx, y + 1)
                    if PrecomputedMoveData.is_valid(x + dx, y + 1):
                        PrecomputedMoveData.pawnAttacksWhite[square].append(idx)
                        PrecomputedMoveData.pawnAttackBitboards[square][0] |= 1 << idx
                if y > 0:
                    idx = PrecomputedMoveData.index(x + dx, y - 1)
                    if PrecomputedMoveData.is_valid(x + dx, y - 1):
                        PrecomputedMoveData.pawnAttacksBlack[square].append(idx)
                        PrecomputedMoveData.pawnAttackBitboards[square][1] |= 1 << idx

        # Direction lookup
        for i in range(127):
            offset = i - 63
            abs_offset = abs(offset)
            if abs_offset % 9 == 0:
                PrecomputedMoveData.directionLookup[i] = 9 * np.sign(offset)
            elif abs_offset % 8 == 0:
                PrecomputedMoveData.directionLookup[i] = 8 * np.sign(offset)
            elif abs_offset % 7 == 0:
                PrecomputedMoveData.directionLookup[i] = 7 * np.sign(offset)
            else:
                PrecomputedMoveData.directionLookup[i] = np.sign(offset)

        # Distance and center masks
        for a in range(64):
            ax, ay = PrecomputedMoveData.coord(a)
            PrecomputedMoveData.CentreManhattanDistance[a] = max(abs(ax - 3), abs(ax - 4)) + max(abs(ay - 3), abs(ay - 4))
            for b in range(64):
                bx, by = PrecomputedMoveData.coord(b)
                PrecomputedMoveData.OrthogonalDistance[a][b] = abs(ax - bx) + abs(ay - by)
                PrecomputedMoveData.kingDistance[a][b] = max(abs(ax - bx), abs(ay - by))

        # Align masks and dir ray mask
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1),
                      (-1, 1), (1, -1), (1, 1), (-1, -1)]
        for a in range(64):
            ax, ay = PrecomputedMoveData.coord(a)
            for b in range(64):
                bx, by = PrecomputedMoveData.coord(b)
                dx, dy = np.sign(bx - ax), np.sign(by - ay)
                if dx == 0 and dy == 0:
                    continue
                for i in range(-8, 9):
                    nx, ny = ax + dx * i, ay + dy * i
                    if PrecomputedMoveData.is_valid(nx, ny):
                        idx = PrecomputedMoveData.index(nx, ny)
                        PrecomputedMoveData.alignMask[a, b] = PrecomputedMoveData.alignMask[a, b] | np.uint64(1 << idx)

        for d, (dx, dy) in enumerate(directions):
            for square in range(64):
                x, y = PrecomputedMoveData.coord(square)
                for i in range(1, 8):
                    nx, ny = x + dx * i, y + dy * i
                    if PrecomputedMoveData.is_valid(nx, ny):
                        idx = PrecomputedMoveData.index(nx, ny)
                        PrecomputedMoveData.dirRayMask[d, square] = PrecomputedMoveData.dirRayMask[d, square] | np.uint64(1 << idx)
                    else:
                        break

# Initialize lookup tables
PrecomputedMoveData.initialize()
