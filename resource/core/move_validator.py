class MoveValidator:
    def __init__(self, board, castling_rights, last_move=None):
        self.board = board
        self.castling_rights = castling_rights  # Format: "KQkq" (White king/queen side, Black king/queen side)
        self.last_move = last_move  
    
    def is_valid_move(self, start_pos, end_pos):
        start_file, start_rank = start_pos
        end_file, end_rank = end_pos
        piece = self.board[start_rank][start_file]
        target_piece = self.board[end_rank][end_file]

        if not piece:
            return False
        
        piece_type = piece[1]
        color = piece[0]
        
        if target_piece and target_piece[0] == color:
            return False
        
        # Check for castling first
        if piece_type == 'K' and abs(start_file - end_file) == 2 and start_rank == end_rank:
            return self.is_valid_castling(start_pos, end_pos, color)
        
        # First check if the move is valid for the piece type
        valid = False
        if piece_type == 'P':
            valid = self.is_valid_pawn_move(start_pos, end_pos, color)
        elif piece_type == 'N':
            valid = self.is_valid_knight_move(start_pos, end_pos)
        elif piece_type == 'B':
            valid = self.is_valid_bishop_move(start_pos, end_pos)
        elif piece_type == 'R':
            valid = self.is_valid_rook_move(start_pos, end_pos)
        elif piece_type == 'Q':
            valid = self.is_valid_queen_move(start_pos, end_pos)
        elif piece_type == 'K':
            valid = self.is_valid_king_move(start_pos, end_pos)
        
        if not valid:
            return False
        
        # Then check if the move would leave the king in check
        return self.is_legal_after_move(start_pos, end_pos, color)
    
    def get_all_valid_moves(self, position):
        valid_moves = []
        for rank in range(8):
            for file in range(8):
                if self.is_valid_move(position, (file, rank)):
                    valid_moves.append((file, rank))
        return valid_moves            
    
    def is_valid_castling(self, start_pos, end_pos, color):
        start_file, start_rank = start_pos
        end_file, end_rank = end_pos

        # King must be on its starting position
        if color == 'w':
            if start_file != 4 or start_rank != 7:
                return False
        else:  # Black
            if start_file != 4 or start_rank != 0:
                return False     

        # King must not be in check
        if self.is_king_in_check(self.board, color):
            return False
        
        # Determine if it's kingside or queenside castling
        if end_file > start_file:  # Kingside (short)
            rook_file = 7
            intermediate_files = [5, 6]
            castling_right = 'K' if color == 'w' else 'k'
        else:  # Queenside (long)
            rook_file = 0
            intermediate_files = [1, 2, 3]
            castling_right = 'Q' if color == 'w' else 'q'
        
        # Check castling rights
        if castling_right not in self.castling_rights:
            return False
        
        # Check if rook is in place
        rook_pos = (rook_file, start_rank)
        rook = self.board[start_rank][rook_file]
        if not rook or rook != color + 'R':
            return False
        
        # Check if squares between king and rook are empty
        for file in intermediate_files:
            if self.board[start_rank][file] != '':
                return False
        
        # Check if king moves through or into check
        king_path = []
        step = 1 if end_file > start_file else -1
        for file in range(start_file, end_file + step, step):
            king_path.append((file, start_rank))
        
        # The first position is where king stands (already checked)
        for pos in king_path[1:]:
            temp_board = [row[:] for row in self.board]
            # Simulate king moving to this position
            temp_board[start_rank][start_file] = ''
            temp_board[pos[1]][pos[0]] = color + 'K'
            if self.is_king_in_check(temp_board, color):
                return False
        
        return True
    
    def is_legal_after_move(self, start, end, color):
        # Create a temporary board to simulate the move
        temp_board = [row[:] for row in self.board]
        piece = temp_board[start[1]][start[0]]

        # Handle en passant capture
        if (piece[1] == 'P' and start[0] != end[0] and temp_board[end[1]][end[0]] == '' and self.last_move):
            last_start, last_end = self.last_move
            last_piece = temp_board[last_end[1]][last_end[0]]
            
            # Check en passant conditions
            if (last_piece and last_piece[1] == 'P' and last_piece[0] != color and
                abs(last_start[1] - last_end[1]) == 2 and
                last_end[0] == end[0] and last_end[1] == start[1]):
                
                # Remove the captured pawn
                temp_board[last_end[1]][last_end[0]] = ''

        temp_board[end[1]][end[0]] = piece
        temp_board[start[1]][start[0]] = ''
        
        # For castling, we also need to move the rook
        piece = temp_board[end[1]][end[0]]
        if piece and piece[1] == 'K' and abs(start[0] - end[0]) == 2:
            # It's a castling move
            if end[0] > start[0]:  # Kingside
                rook_start = (7, end[1])
                rook_end = (5, end[1])
            else:  # Queenside
                rook_start = (0, end[1])
                rook_end = (3, end[1])
            
            temp_board[rook_end[1]][rook_end[0]] = temp_board[rook_start[1]][rook_start[0]]
            temp_board[rook_start[1]][rook_start[0]] = ''
        
        # Check if the king is in check after the move
        return not self.is_king_in_check(temp_board, color)
    
    def is_king_in_check(self, board, color):
        king_pos = None
        # Find the king's position
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece and piece == color + 'K':
                    king_pos = (file, rank)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        # Check if any opponent's piece can attack the king
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece and piece[0] != color:
                    if self.is_direct_attack((file, rank), king_pos, board):
                        return True
        return False

    def is_direct_attack(self, start, end, board):
        if end is None:
            # Check if any opponent piece can attack the start position
            start_file, start_rank = start
            piece = board[start_rank][start_file]
            if not piece:
                return False
            color = piece[0]
            opponent_color = 'w' if color == 'b' else 'b'
            
            for rank in range(8):
                for file in range(8):
                    p = board[rank][file]
                    if p and p[0] == opponent_color:
                        # Check if this piece can attack start
                        piece_type = p[1]
                        if piece_type == 'P':
                            direction = -1 if p[0] == 'w' else 1
                            if (abs(file - start_file) == 1 and 
                                start_rank == rank + direction):
                                return True
                        elif piece_type == 'N':
                            if (abs(file - start_file), abs(rank - start_rank)) in [(1, 2), (2, 1)]:
                                return True
                        elif piece_type in ['B', 'R', 'Q']:
                            if (piece_type == 'B' and self.is_valid_bishop_move((file, rank), start, board)) or \
                               (piece_type == 'R' and self.is_valid_rook_move((file, rank), start, board)) or \
                               (piece_type == 'Q' and (self.is_valid_bishop_move((file, rank), start, board) or 
                                                       self.is_valid_rook_move((file, rank), start, board))):
                                return True
                        elif piece_type == 'K':
                            if max(abs(file - start_file), abs(rank - start_rank)) == 1:
                                return True
            return False

        start_file, start_rank = start
        end_file, end_rank = end
        piece = board[start_rank][start_file]

        if not piece:
            return False
        
        piece_type = piece[1]
        color = piece[0]
        
        if piece_type == 'P':
            direction = -1 if color == 'w' else 1
            return (abs(start_file - end_file) == 1 and end_rank == start_rank + direction)
        elif piece_type == 'N':
            return (abs(start_file - end_file), abs(start_rank - end_rank)) in [(1, 2), (2, 1)]
        elif piece_type == 'B':
            return self.is_valid_bishop_move(start, end, board)
        elif piece_type == 'R':
            return self.is_valid_rook_move(start, end, board)
        elif piece_type == 'Q':
            return (self.is_valid_bishop_move(start, end, board) or 
                    self.is_valid_rook_move(start, end, board))
        elif piece_type == 'K':
            return max(abs(start_file - end_file), abs(start_rank - end_rank)) == 1
        
        return False
    
    def is_valid_pawn_move(self, start_pos, end_pos, piece_color):
        start_file, start_rank = start_pos
        end_file, end_rank = end_pos
        direction = -1 if piece_color == 'w' else 1  # Trắng đi lên (-1), đen đi xuống (+1)

        # Đi thẳng một ô
        if end_file == start_file and end_rank == start_rank + direction:
            if self.board[end_rank][end_file] == '':
                return True

        # Đi hai ô từ vị trí ban đầu
        if end_file == start_file and end_rank == start_rank + 2 * direction:
            if (piece_color == 'w' and start_rank == 6) or (piece_color == 'b' and start_rank == 1):
                if self.board[start_rank + direction][start_file] == '' and self.board[end_rank][end_file] == '':
                    return True

        # Ăn chéo bình thường
        if abs(end_file - start_file) == 1 and end_rank == start_rank + direction:
            if self.board[end_rank][end_file] and self.board[end_rank][end_file][0] != piece_color:
                return True

        # Bắt tốt qua đường (en passant)
        if abs(end_file - start_file) == 1 and end_rank == start_rank + direction and self.board[end_rank][end_file] == '':
            if self.last_move:
                last_start, last_end = self.last_move
                last_piece = self.board[last_end[1]][last_end[0]]
                
                # Kiểm tra điều kiện en passant
                if (last_piece and last_piece[1] == 'P' and last_piece[0] != piece_color and
                    abs(last_start[1] - last_end[1]) == 2 and  # Tốt đã đi 2 ô
                    last_end[0] == end_file and  # Cùng cột với vị trí bắt
                    last_end[1] == start_rank):  # Cùng hàng với tốt đang đi
                    return True

        return False
    
    def is_valid_knight_move(self, start, end, board=None):
        dx = abs(start[0] - end[0])
        dy = abs(start[1] - end[1])
        return (dx, dy) in [(1, 2), (2, 1)]
    
    def is_valid_bishop_move(self, start, end, board=None):
        if board is None:
            board = self.board
        if abs(start[0] - end[0]) != abs(start[1] - end[1]):
            return False
        
        file_step = 1 if end[0] > start[0] else -1
        rank_step = 1 if end[1] > start[1] else -1
        
        file, rank = start[0] + file_step, start[1] + rank_step
        while (file, rank) != end:
            if board[rank][file] != '':
                return False
            file += file_step
            rank += rank_step
        
        return True
    
    def is_valid_rook_move(self, start, end, board=None):
        if board is None:
            board = self.board
        if start[0] != end[0] and start[1] != end[1]:
            return False
        
        if start[0] == end[0]:
            step = 1 if end[1] > start[1] else -1
            for rank in range(start[1] + step, end[1], step):
                if board[rank][start[0]] != '':
                    return False
        else:
            step = 1 if end[0] > start[0] else -1
            for file in range(start[0] + step, end[0], step):
                if board[start[1]][file] != '':
                    return False
        
        return True
    
    def is_valid_queen_move(self, start, end, board=None):
        if board is None:
            board = self.board
        return (self.is_valid_bishop_move(start, end, board) or 
                self.is_valid_rook_move(start, end, board))
    
    def is_valid_king_move(self, start, end, board=None):
        return max(abs(start[0] - end[0]), abs(start[1] - end[1])) == 1
    
    def is_stalemate(self, color):
        """Kiểm tra hòa do hết nước đi"""
        if self.is_king_in_check(self.board, color):
            return False
            
        for rank in range(8):
            for file in range(8):
                piece = self.board[rank][file]
                if piece and piece[0] == color:
                    if self.get_all_valid_moves((file, rank)):
                        return False
        return True

    # --- Phương thức mới được thêm ---
    def is_checkmate(self, color):
        """Check if the given color is in checkmate"""
        if not self.is_king_in_check(self.board, color):
            return False

        # Check if any move can escape check
        for rank in range(8):
            for file in range(8):
                piece = self.board[rank][file]
                if piece and piece[0] == color:
                    start_pos = (file, rank)
                    valid_moves = self.get_all_valid_moves(start_pos)
                    for end_pos in valid_moves:
                        # Try the move on a temporary board
                        temp_board = [row[:] for row in self.board]
                        piece = temp_board[start_pos[1]][start_pos[0]]
                        temp_board[end_pos[1]][end_pos[0]] = piece
                        temp_board[start_pos[1]][start_pos[0]] = ''
                        # Handle pawn promotion
                        if piece[1] == 'P' and (end_pos[1] == 0 or end_pos[1] == 7):
                            temp_board[end_pos[1]][end_pos[0]] = color + 'Q'
                        if not self.is_king_in_check(temp_board, color):
                            return False  # Found a move to escape check
        return True  # No move can escape check, it's checkmate

    def execute_move(self, board, start_pos, end_pos):
        """Execute a move on the board for simulation"""
        start_file, start_rank = start_pos
        end_file, end_rank = end_pos
        piece = board[start_rank][start_file]
        board[end_rank][end_file] = piece
        board[start_rank][start_file] = ''
        # Handle pawn promotion
        if piece and piece[1] == 'P' and (end_rank == 0 or end_rank == 7):
            board[end_rank][end_file] = piece[0] + 'Q'
        # Handle en passant
        if (piece[1] == 'P' and start_file != end_file and 
            board[end_rank][end_file] == '' and self.last_move):
            last_start, last_end = self.last_move
            if (abs(last_start[1] - last_end[1]) == 2 and 
                last_end[0] == end_file and last_end[1] == start_rank):
                board[last_end[1]][last_end[0]] = ''
        # Handle castling
        if piece[1] == 'K' and abs(start_file - end_file) == 2:
            if end_file > start_file:  # Kingside
                rook_start = (7, start_rank)
                rook_end = (5, start_rank)
            else:  # Queenside
                rook_start = (0, start_rank)
                rook_end = (3, start_rank)
            board[rook_end[1]][rook_end[0]] = board[rook_start[1]][rook_start[0]]
            board[rook_start[1]][rook_start[0]] = ''