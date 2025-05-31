from evaluation import PIECE_VALUES

def detect_forks(board, move_validator, color):
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    forks = []
    enemy_color = 'b' if color == 'w' else 'w'

    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece[0] == color and piece[1] == 'N':  # Only knight forks for now
                attacks = []
                for dy, dx in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                               (1, -2), (1, 2), (2, -1), (2, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = board[ny][nx]
                        if target and target[0] == enemy_color:
                            if move_validator.is_valid_move((x, y), (nx, ny)):
                                attacks.append((nx, ny))
                if len(attacks) >= 2:
                    forks.append(((x, y), attacks))
    return forks

def detect_pins(board, move_validator, color):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    pins = []
    enemy_color = 'b' if color == 'w' else 'w'
    king_pos = None

    # Find king position
    for y in range(8):
        for x in range(8):
            if board[y][x] == color + 'K':
                king_pos = (x, y)
                break
        if king_pos:
            break

    if not king_pos:
        return pins

    kx, ky = king_pos

    for dx, dy in directions:
        blockers = []
        x, y = kx + dx, ky + dy
        while 0 <= x < 8 and 0 <= y < 8:
            piece = board[y][x]
            if piece:
                if piece[0] == color:
                    if len(blockers) == 0:
                        blockers.append((x, y))
                    else:
                        break
                else:
                    ptype = piece[1]
                    if len(blockers) == 1 and (
                        (ptype in ['Q']) or
                        (ptype == 'R' and (dx == 0 or dy == 0)) or
                        (ptype == 'B' and dx != 0 and dy != 0)
                    ):
                        pins.append((blockers[0], (x, y)))  # (pinned piece, pinner)
                    break
            x += dx
            y += dy

    return pins

def detect_skewers(board, move_validator, color):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    enemy_color = 'b' if color == 'w' else 'w'
    skewers = []

    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece[0] == color and piece[1] in ['Q', 'R', 'B']:
                for dx, dy in directions:
                    # filter direction based on piece type
                    if piece[1] == 'R' and (dx != 0 and dy != 0): continue
                    if piece[1] == 'B' and (dx == 0 or dy == 0): continue

                    ray = []
                    tx, ty = x + dx, y + dy
                    while 0 <= tx < 8 and 0 <= ty < 8:
                        target = board[ty][tx]
                        if target:
                            ray.append(((tx, ty), target))
                        if len(ray) == 2:
                            if ray[0][1][0] == enemy_color and ray[1][1][0] == enemy_color:
                                v1 = PIECE_VALUES[ray[0][1][1]]
                                v2 = PIECE_VALUES[ray[1][1][1]]
                                if v1 > v2:
                                    skewers.append(((x, y), ray[0][0], ray[1][0]))
                            break
                        tx += dx
                        ty += dy
    return skewers

def detect_discovered_attacks(board, move_validator, color):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    discovered_attacks = []
    enemy_color = 'b' if color == 'w' else 'w'

    for y in range(8):
        for x in range(8):
            blocker = board[y][x]
            if not blocker or blocker[0] != color:
                continue

            for dx, dy in directions:
                behind_path = []
                bx, by = x + dx, y + dy
                while 0 <= bx < 8 and 0 <= by < 8:
                    target = board[by][bx]
                    if target:
                        if target[0] == color and target[1] in ['R', 'B', 'Q']:
                            # We've found a friendly sliding piece that could be revealed
                            # Now scan beyond it for enemy target
                            tx, ty = bx + dx, by + dy
                            while 0 <= tx < 8 and 0 <= ty < 8:
                                victim = board[ty][tx]
                                if victim and victim[0] == enemy_color:
                                    if move_validator.is_valid_move((x, y), (x+1 if x<7 else x-1, y)):  # simple escape
                                        discovered_attacks.append(((x, y), (bx, by), (tx, ty)))
                                    break
                                elif victim:
                                    break
                                tx += dx
                                ty += dy
                        break
                    bx += dx
                    by += dy
    return discovered_attacks