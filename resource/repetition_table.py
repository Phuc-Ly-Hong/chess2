from collections import defaultdict

class RepetitionTable:
    def __init__(self):
        self.position_counts = defaultdict(int)
        self.position_history = []

    def push(self, zobrist_hash):
        self.position_counts[zobrist_hash] += 1
        self.position_history.append(zobrist_hash)

    def pop(self):
        if self.position_history:
            hash = self.position_history.pop()
            self.position_counts[hash] -= 1
            if self.position_counts[hash] == 0:
                del self.position_counts[hash]

    def is_repetition(self, zobrist_hash):
        return self.position_counts[zobrist_hash] >= 3

    def reset(self):
        self.position_counts.clear()
        self.position_history.clear()
