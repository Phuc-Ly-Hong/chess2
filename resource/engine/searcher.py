import time
from typing import List, Tuple, Optional
from core.move_generator import MoveGenerator
from core.board_wrapper import BoardWrapper
from engine.evaluation import Evaluation
from engine.repetition_table import RepetitionTable
from engine.zobrist import ZobristHasher
from engine.move_odering import MoveOrdering

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
        self.time_limit = 10.0  # Default time limit in seconds
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

    def quiescence_search(self, board: BoardWrapper, alpha: int, beta: int, depth: int = 6) -> int:
        self.nodes += 1

        # Giới hạn thời gian và độ sâu
        if time.time() - self.start_time > self.time_limit or self.stop_search or depth <= 0:
            self.stop_search = True
            return self.evaluation.evaluate(board)

        stand_pat = self.evaluation.evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Futility pruning nhẹ: nếu đánh giá đứng yên + biên thấp hơn alpha thì bỏ qua nước
        futility_margin = 100
        if stand_pat + futility_margin < alpha:
            return alpha

        moves = self.move_generator.generate_moves(board, captures_only=True)
        moves = self.move_ordering.order_moves(moves, 0, board=board)

        for move in moves:
            # Bỏ qua nước ăn lỗ theo SEE
            if self.move_ordering.see(board, move[1], move[0]) < 0:
                continue

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
        self.nodes += 1

        # Ngừng nếu hết thời gian
        if self.stop_search or time.time() - self.start_time > self.time_limit:
            self.stop_search = True
            return 0, None

        # Kiểm tra lặp lại
        zobrist_hash = self.zobrist.hash(board)
        if self.repetition_table.is_repetition(zobrist_hash):
            return 0, None

        in_check = self.move_generator.is_king_in_check(board, board.turn)

        # Quiescence nếu hết độ sâu
        if depth <= 0:
            return self.quiescence_search(board, alpha, beta), None

        # Null Move Pruning
        if not in_check and depth >= 3:
            piece_count = sum(
                1 for sq in range(64)
                if board.get_piece(sq) and board.get_piece(sq)[1] not in ['K', 'k']
            )
            if piece_count > 4:
                null_board = board.make_copy_and_apply(("null", "null"))
                null_board.turn = 'b' if board.turn == 'w' else 'w'
                R = 2 if depth < 5 else 3
                null_score = -self.alpha_beta(null_board, depth - R, -beta, -beta + 1, ply + 1)[0]
                if null_score >= beta:
                    return beta, None

        # Tra bảng lặp lại
        tt_score, tt_move = self.probe_transposition(zobrist_hash, depth, alpha, beta)
        if tt_score is not None:
            return tt_score, tt_move

        # Sinh nước đi
        moves = self.move_generator.generate_moves(board)
        if not moves:
            if in_check:
                return -1000000 + ply, None
            return 0, None

        # Move Ordering
        moves = self.move_ordering.order_moves(moves, ply, board=board, pv_move=pv_move, tt_move=tt_move)

        best_score = -float('inf')
        best_move = None
        flag = 'upper'
        last_move = board.last_move

        for i, move in enumerate(moves):
            # Skip nếu capture xấu theo SEE
            if board.is_capture(move) and self.move_ordering.see(board, move[1], move[0]) < 0:
                continue

            new_board = board.make_copy_and_apply(move)
            new_hash = self.zobrist.hash(new_board)
            self.repetition_table.push(new_hash)

            # PVS và LMR
            if i == 0:
                score, _ = self.alpha_beta(new_board, depth - 1, -beta, -alpha, ply + 1)
            else:
                reduced_depth = depth - 1
                if (
                    depth >= 3 and not in_check and not board.is_capture(move)
                    and not board.move_gives_check(move) and i >= 3
                ):
                    reduced_depth = depth - 2

                score, _ = self.alpha_beta(new_board, reduced_depth, -alpha - 1, -alpha, ply + 1)
                if alpha < score < beta:
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
                if last_move and isinstance(last_move, tuple) and isinstance(last_move[1], int):
                    self.move_ordering.add_counter_move(last_move, move)
                break

        self.store_transposition(zobrist_hash, depth, best_score, flag, best_move)
        return best_score, best_move

    def search(self, board: BoardWrapper, time_limit: float = 10.0, max_depth: int = 6) -> Optional[Tuple]:
        """Khởi động tìm kiếm và trả về nước đi tốt nhất."""
        print(f"[DEBUG] Bat dau search voi time_limit={time_limit}")
        self.time_limit = time_limit
        best_move, score = self.iterative_deepening(board, max_depth=max_depth, time_limit=time_limit)
        print(f"[DEBUG] Ket thuc search, best_move={best_move}, score={score}")
        return best_move

    def iterative_deepening(self, board: BoardWrapper, max_depth: int = 6, time_limit: Optional[float] = None) -> Tuple[Optional[Tuple], int]:
        """Tìm kiếm lặp sâu dần với giới hạn độ sâu và thời gian, có Aspiration Windows và quản lý thời gian động."""
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
            # Dynamic Time Management: Ngắt nếu không còn đủ thời gian
            elapsed = time.time() - self.start_time
            remaining = self.time_limit - elapsed
            if remaining < 0.2:
                print(f"[DEBUG] Dung lai vi thoi gian con lai qua it ({remaining:.2f}s)")
                self.stop_search = True
                break

            print(f"[DEBUG] Tim kiem o do sau {depth}")

            # Aspiration Window: Dùng khoảng alpha-beta hẹp trước
            aspiration_window = 100
            alpha = max(best_score - aspiration_window, -100000)
            beta = min(best_score + aspiration_window, 100000)

            score, move = self.alpha_beta(board, depth, alpha, beta, 0, pv_move)

            # Nếu fail-low hoặc fail-high thì dùng full window
            if score <= alpha or score >= beta:
                print(f"[DEBUG] Fail aspiration window, mo rong cua so alpha-beta")
                score, move = self.alpha_beta(board, depth, -100000, 100000, 0, pv_move)

            if self.stop_search:
                print(f"[DEBUG] Dung lai vi het thoi gian tai do sau {depth}")
                break

            if move is None:
                print(f"[DEBUG] Do sau {depth}: Khong tim thay nuoc di hoac bi dung")
                break

            best_score = score
            best_move = move
            pv_move = move

        return best_move, best_score


