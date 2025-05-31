class TTEntry:
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2

    def __init__(self, zobrist_key, depth, score, flag, move):
        self.zobrist_key = zobrist_key
        self.depth = depth
        self.score = score
        self.flag = flag
        self.move = move

class TranspositionTable:
    def __init__(self):
        self.table = {}

    def store(self, zobrist_key, depth, score, flag, move):
        if zobrist_key in self.table:
            entry = self.table[zobrist_key]
            if depth >= entry.depth:
                self.table[zobrist_key] = TTEntry(zobrist_key, depth, score, flag, move)
        else:
            self.table[zobrist_key] = TTEntry(zobrist_key, depth, score, flag, move)

    def probe(self, zobrist_key):
        return self.table.get(zobrist_key, None)

    def clear(self):
        self.table.clear()
