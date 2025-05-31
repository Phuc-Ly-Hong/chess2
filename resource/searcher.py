import time
from typing import List, Tuple, Optional
from move_generator import MoveGenerator
from board_wrapper import BoardWrapper
from evaluation import Evaluation
from repetition_table import RepetitionTable
from zobrist import ZobristHasher
from move_odering import MoveOrdering

class Search:
    def __init__(self):
        self.move_generator = MoveGenerator()
        self.evaluation = Evaluation()
        self.repetition_table = RepetitionTable()
        self.zobrist = ZobristHasher()
        self.move_ordering = MoveOrdering()
        self.transposition_table = {}  # {zobrist_hash: {depth, score, flag, move}}
        self.nodes = 0
        self.max_depth = 64
        self.time_limit = 5.0  # Default time limit in seconds
        self.start_time = 0
        self.stop_search = False
        self.best_move = None

    def store_transposition(self, zobrist_hash: int, depth: int, score: int, flag: str, move: Tuple):
        """Store position in transposition table."""
        self.transposition_table[zobrist_hash] = {
            'depth': depth,
            'score': score,
            'flag': flag,  # 'exact', 'lower', 'upper'
            'move': move
        }

    def probe_transposition(self, zobrist_hash: int, depth: int, alpha: int, beta: int) -> Tuple[Optional[int], Optional[Tuple]]:
        """Probe transposition table for a stored position."""
        entry = self.transposition_table.get(zobrist_hash)
        if entry and entry['depth'] >= depth:
            score = entry['score']
            if entry['flag'] == 'exact':
                return score, entry['move']
            elif entry['flag'] == 'lower' and score >= beta:
                return beta, entry['move']
            elif entry['flag'] == 'upper' and score <= alpha:
                return alpha, entry['move']
        return None, None

    def quiescence_search(self, board: BoardWrapper, alpha: int, beta: int, depth: int = 4) -> int:
        """Perform quiescence search to evaluate captures and avoid horizon effect."""
        self.nodes += 1
        if self.stop_search or time.time() - self.start_time > self.time_limit or depth <= 0:
            self.stop_search = True
            return self.evaluation.evaluate(board)

        stand_pat = self.evaluation.evaluate(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        moves = self.move_generator.generate_moves(board, captures_only=True)
        moves = self.move_ordering.order_moves(moves, 0, board=board)  # Depth 0 for quiescence

        for move in moves:
            new_board = board.make_copy_and_apply(move)
            score = -self.quiescence_search(new_board, -beta, -alpha, depth - 1)
            if self.stop_search:
                return 0
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def alpha_beta(self, board: BoardWrapper, depth: int, alpha: int, beta: int, ply: int, pv_move: Optional[Tuple] = None) -> Tuple[int, Optional[Tuple]]:
        """Alpha-beta pruning search."""
        self.nodes += 1
        if self.stop_search or time.time() - self.start_time > self.time_limit:
            self.stop_search = True
            return 0, None

        zobrist_hash = self.zobrist.hash(board)
        if self.repetition_table.is_repetition(zobrist_hash):
            return 0, None  # Draw by repetition

        if depth <= 0:
            return self.quiescence_search(board, alpha, beta), None

        # Probe transposition table
        tt_score, tt_move = self.probe_transposition(zobrist_hash, depth, alpha, beta)
        if tt_score is not None:
            return tt_score, tt_move

        moves = self.move_generator.generate_moves(board)
        if not moves:
            if self.move_generator.is_king_in_check(board, board.turn):
                return -1000000 + ply, None  # Checkmate
            return 0, None  # Stalemate

        # Order moves using MoveOrdering
        moves = self.move_ordering.order_moves(moves, ply,board = board, pv_move=pv_move, tt_move=tt_move)
        best_move = moves[0]
        best_score = -float('inf')
        flag = 'upper'

        last_move = board.last_move
        for move in moves:
            new_board = board.make_copy_and_apply(move)
            new_hash = self.zobrist.hash(new_board)
            self.repetition_table.push(new_hash)

            score, _ = self.alpha_beta(new_board, depth - 1, -beta, -alpha, ply + 1)
            score = -score
            self.repetition_table.pop()

            if self.stop_search:
                return 0, None

            if score > best_score:
                best_score = score
                best_move = move
                if score > alpha:
                    alpha = score
                    flag = 'exact'
                if score >= beta:
                    flag = 'lower'
                    self.move_ordering.add_killer(ply, move)
                    self.move_ordering.add_history(move, depth)
                    self.move_ordering.add_counter_move(last_move, move)
                    break

        self.store_transposition(zobrist_hash, depth, best_score, flag, best_move)
        return best_score, best_move

    def search(self, board: BoardWrapper, time_limit: float = 5.0, max_depth: int = 6) -> Optional[Tuple]:
        """Khởi động tìm kiếm và trả về nước đi tốt nhất."""
        print(f"[DEBUG] Bat dau search voi time_limit={time_limit}")
        self.time_limit = time_limit
        best_move, score = self.iterative_deepening(board, max_depth=max_depth, time_limit=time_limit)
        print(f"[DEBUG] Ket thuc search, best_move={best_move}, score={score}")
        return best_move

    def iterative_deepening(self, board: BoardWrapper, max_depth: int = 6, time_limit: Optional[float] = None) -> Tuple[Optional[Tuple], int]:
        """Tìm kiếm lặp sâu dần với giới hạn độ sâu và thời gian."""
        print(f"[DEBUG] Bat dau iterative_deepening voi max_depth={max_depth}, time_limit={time_limit}")
        self.nodes = 0
        self.start_time = time.time()
        self.stop_search = False
        self.best_move = None
        self.transposition_table.clear()
        self.repetition_table.reset()

        if time_limit is not None:
            self.time_limit = time_limit

        best_move = None
        best_score = 0
        pv_move = None

        for depth in range(1, max_depth + 1):
            if self.stop_search:
                break

            print(f"[DEBUG] Tim kiem o do sau {depth}")
            score, move = self.alpha_beta(board, depth, -1_000_000, 1_000_000, 0, pv_move)

            if self.stop_search:
                print(f"[DEBUG] Dung lai vi het thoi gian tai do sau {depth}")
                break

            if move is None:
                print(f"[DEBUG] do sau {depth}: Khong tim thay nuoc di hoac bi dung")
                break

            best_score = score
            best_move = move
            pv_move = move

        return best_move, best_score

