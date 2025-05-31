import random
import math

class BookMove:
    def __init__(self, move_string, num_times_played):
        self.move_string = move_string
        self.num_times_played = num_times_played

class OpeningBook:
    def __init__(self, file_content=None, file_path=None):
        self.moves_by_position = {}
        self.rng = random.Random()

        if file_content:
            self.load_from_string(file_content)
        elif file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    print("Content of Book.txt:\n", content)  # Debug nội dung file
                    self.load_from_string(content)
                print("Successfully loaded opening book with", len(self.moves_by_position), "positions")  # Debug số lượng vị trí
            except Exception as e:
                print(f"Failed to load opening book from {file_path}: {e}")

    def load_from_string(self, content):
        entries = [e.strip() for e in content.strip().split("pos")[1:] if e.strip()]
        for entry in entries:
            entry_data = entry.strip().split('\n')
            position_fen = entry_data[0].strip()
            move_data = entry_data[1:]
            book_moves = []
            for move_line in move_data:
                move_string, num_played = move_line.split()
                book_moves.append(BookMove(move_string, int(num_played)))
            self.moves_by_position[self.remove_move_counters_from_fen(position_fen)] = book_moves

    def has_book_move(self, position_fen):
        return self.remove_move_counters_from_fen(position_fen) in self.moves_by_position

    def try_get_book_move(self, board, color, turn, castling_rights, last_move, weight_pow=0.5):
        position_fen = self.get_current_fen(board, turn, castling_rights, last_move)
        print(f"\n[Opening Book] Current position FEN: {position_fen}")
    
        fen_key = self.remove_move_counters_from_fen(position_fen)
        print(f"[Opening Book] Lookup key: {fen_key}")
    
        if fen_key in self.moves_by_position:
            moves = self.moves_by_position[fen_key]
            print(f"[Opening Book] Found {len(moves)} book moves for this position")
        
            for i, move in enumerate(moves[:5]):
                print(f"  {i+1}. {move.move_string} (played {move.num_times_played} times)")
            
            total_play_count = sum(m.num_times_played ** weight_pow for m in moves)
            weights = [(m.num_times_played ** weight_pow) / total_play_count for m in moves]
        
            selected_move = random.choices(moves, weights=weights, k=1)[0]
            print(f"[Opening Book] Selected move: {selected_move.move_string}")
        
            move_coords = self.algebraic_to_coords(selected_move.move_string, board, color)
            if move_coords:
                print(f"[Opening Book] Converted to coordinates: {move_coords}")
                return move_coords
            else:
                print("[Opening Book] Failed to convert move to coordinates")
        else:
            print("[Opening Book] No book moves found for this position")
    
        return None

    def weighted_play_count(self, play_count, weight_pow):
        return math.ceil(play_count ** weight_pow)

    def remove_move_counters_from_fen(self, fen):
        parts = fen.rsplit()
        if len(parts) >= 4:
            return ' '.join(parts[:4])
        return fen

    def get_current_fen(self, board, turn, castling_rights, last_move):
        fen_parts = []
        
        for rank in board:
            rank_str = ""
            empty_count = 0
            
            for piece in rank:
                if not piece or len(piece) < 2:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    
                    color, ptype = piece[0], piece[1]
                    rank_str += ptype.lower() if color == 'b' else ptype.upper()
                    
            if empty_count > 0:
                rank_str += str(empty_count)
            fen_parts.append(rank_str)
        
        fen = '/'.join(fen_parts)
        
        fen += ' ' + ('w' if turn else 'b')
        fen += ' ' + (castling_rights if castling_rights else '-')
        
        if last_move:
            start, end = last_move
            piece = board[start[1]][start[0]]
            if piece and piece[1] == 'P' and abs(start[1] - end[1]) == 2:
                fen += ' ' + ('abcdefgh'[end[0]] + str(8 - end[1]))
            else:
                fen += ' -'
        else:
            fen += ' -'
        
        fen += ' 0 1'
        return fen

    def algebraic_to_coords(self, move, board, color):
        if len(move) == 4 and move[0].islower() and move[1].isdigit() and move[2].islower() and move[3].isdigit():
            try:
                start_file = ord(move[0]) - ord('a')
                start_rank = 8 - int(move[1])
                end_file = ord(move[2]) - ord('a')
                end_rank = 8 - int(move[3])

                if not (0 <= start_file < 8 and 0 <= start_rank < 8 and 0 <= end_file < 8 and 0 <= end_rank < 8):
                    return None
                
                piece = board[start_rank][start_file]
                if not piece or piece[0].lower() != color.lower():
                    return None
                
                return ((start_file, start_rank), (end_file, end_rank))
            except:
                return None
        return None
