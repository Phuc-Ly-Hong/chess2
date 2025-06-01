# Precomputed pawn shield squares and distances for evaluation
import numpy as np

PawnShieldSquaresWhite = [[] for _ in range(64)]
PawnShieldSquaresBlack = [[] for _ in range(64)]
OrthogonalDistance = np.zeros((64, 64), dtype=np.int8)
CentreManhattanDistance = np.zeros(64, dtype=np.int8)

def is_valid(file, rank):
    return 0 <= file < 8 and 0 <= rank < 8

def index(file, rank):
    return rank * 8 + file

# Compute pawn shield squares
for square in range(64):
    file = square % 8
    rank = square // 8
    clamped_file = max(1, min(6, file))

    for offset in [-1, 0, 1]:
        for forward in [1, 2]:
            fx = clamped_file + offset
            fy_white = rank + forward
            fy_black = rank - forward

            if is_valid(fx, fy_white):
                PawnShieldSquaresWhite[square].append(index(fx, fy_white))
            if is_valid(fx, fy_black):
                PawnShieldSquaresBlack[square].append(index(fx, fy_black))

# Compute distance maps
for a in range(64):
    ax, ay = a % 8, a // 8
    CentreManhattanDistance[a] = max(abs(ax - 3), abs(ax - 4)) + max(abs(ay - 3), abs(ay - 4))
    for b in range(64):
        bx, by = b % 8, b // 8
        OrthogonalDistance[a][b] = abs(ax - bx) + abs(ay - by)
