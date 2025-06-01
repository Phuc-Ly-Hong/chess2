import pygame
import os
import copy
from move_validator import MoveValidator 
from bot import ChessBot
from board_wrapper import BoardWrapper
import threading

# Initialize pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 850, 850
SQUARE_SIZE = WIDTH // 8  # Size of each square
  
# Colors
LIGHT_COLOR = (238, 238, 210)
DARK_COLOR = (118, 150, 86)
TEXT_COLOR = (0, 0, 0)

# Thêm vào phần khai báo biến toàn cục
valid_moves = []  # Lưu trữ các nước đi hợp lệ
highlight_color = (100, 200, 255, 100)  # Màu xanh nhạt trong suốt để highlight

# Font for coordinates
pygame.font.init()
FONT = pygame.font.SysFont("Arial", 24)

# Create window
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Board")

# Path to assets directory
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

import pygame
import os

pygame.mixer.init()     

# Load chess pieces images
def load_pieces():
    pieces = {}
    piece_names = ['K', 'Q', 'R', 'B', 'N', 'P']
    colors = {'w': 'white', 'b': 'black'}

    for color_prefix, color_name in colors.items():
        for piece in piece_names:
            image_path = os.path.join(ASSETS_DIR, f"{color_prefix}{piece}.png")
            try:
                img = pygame.image.load(image_path)
                img = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
                pieces[f"{color_name}_{piece}"] = img
            except Exception as e:
                print(f"Unable to load image: {image_path} with error {e}")
    return pieces

# Load pieces images
pieces = load_pieces()

# Initial board setup
initial_board = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
]

castling_rights = "KQkq"  # K=White kingside, Q=White queenside, k=Black kingside, q=Black queenside
last_move = None
move_validator = MoveValidator(initial_board, castling_rights, last_move)
promoting_pawn = None  # Lưu trữ vị trí quân tốt cần phong cấp
promotion_pieces = ['Q', 'R', 'B', 'N']  # Các loại quân có thể phong cấp thành
history_stack = []
redo_stack = []

# Variables for game state
selected_piece = None
selected_pos = None
turn = True  # True for white, False for black
game_over = False
winner = None
bot_thinking = False
bot = None

def highlight_last_move():
    if last_move:
        (start_file, start_rank), (end_file, end_rank) = last_move
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill((100, 200, 255, 100)) 
        win.blit(highlight_surface, (start_file * SQUARE_SIZE, start_rank * SQUARE_SIZE))
        win.blit(highlight_surface, (end_file * SQUARE_SIZE, end_rank * SQUARE_SIZE))

def draw_board():
    for file in range(8):
        for rank in range(8):
            is_light_square = (file + rank) % 2 == 0
            color = LIGHT_COLOR if is_light_square else DARK_COLOR
            pygame.draw.rect(win, color, (file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
            # Vẽ highlight cho các ô có thể di chuyển
            if selected_piece and (file, rank) in valid_moves:
                highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                highlight.fill(highlight_color)
                win.blit(highlight, (file * SQUARE_SIZE, rank * SQUARE_SIZE))
            
            piece_code = initial_board[rank][file]
            if piece_code:
                color_prefix = piece_code[0]
                piece_name = piece_code[1]
                color_name = 'white' if color_prefix == 'w' else 'black'
                piece_key = f"{color_name}_{piece_name}"
                if piece_key in pieces:
                    win.blit(pieces[piece_key], (file * SQUARE_SIZE, rank * SQUARE_SIZE))
    
    # Vẽ highlight nước đi gần nhất
    highlight_last_move()                

    if promoting_pawn:
        pawn_color = initial_board[promoting_pawn[1]][promoting_pawn[0]][0]
        draw_promotion_menu(pawn_color)

    for i in range(8):
        rank_text = FONT.render(str(8 - i), True, TEXT_COLOR)
        win.blit(rank_text, (5, i * SQUARE_SIZE + 5))
        file_text = FONT.render(chr(97 + i), True, TEXT_COLOR)
        win.blit(file_text, (i * SQUARE_SIZE + SQUARE_SIZE - 20, HEIGHT - 25))

def display_game_result(winner):
    win.fill((0, 0, 0, 180))  # Màn hình tối mờ
    font = pygame.font.SysFont("Arial", 50)
    
    if winner:
        text = f"{'White' if winner == 'w' else 'Black'} wins!"
        color = (255, 255, 255) if winner == 'w' else (200, 200, 200)
    else:
        text = "Game ended in draw!"
        color = (200, 200, 0)
    
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
    win.blit(text_surface, text_rect)
    
    # Hiển thị hướng dẫn tiếp tục
    small_font = pygame.font.SysFont("Arial", 30)
    continue_text = small_font.render("Press any key to close", True, (255, 255, 255))
    win.blit(continue_text, (WIDTH//2 - 150, HEIGHT//2 + 60))

# Function to get the square at the mouse position
def get_square_at_pos(mouse_pos):
    x, y = mouse_pos
    return x // SQUARE_SIZE, y // SQUARE_SIZE

def update_castling_rights(piece_moved, start_pos):
    global castling_rights
    
    start_file, start_rank = start_pos
    
    # If the king moves, remove all castling rights for that color
    if piece_moved[1] == 'K':
        if piece_moved[0] == 'w':  # White king
            castling_rights = castling_rights.replace('K', '').replace('Q', '')
        else:  # Black king
            castling_rights = castling_rights.replace('k', '').replace('q', '')
    
    # If a rook moves from its starting position, remove its specific castling right
    elif piece_moved[1] == 'R':
        # White rooks
        if piece_moved[0] == 'w':
            if start_file == 0 and start_rank == 7:  # Queenside rook (a1)
                castling_rights = castling_rights.replace('Q', '')
            elif start_file == 7 and start_rank == 7:  # Kingside rook (h1)
                castling_rights = castling_rights.replace('K', '')
        # Black rooks
        else:
            if start_file == 0 and start_rank == 0:  # Queenside rook (a8)
                castling_rights = castling_rights.replace('q', '')
            elif start_file == 7 and start_rank == 0:  # Kingside rook (h8)
                castling_rights = castling_rights.replace('k', '')
    
    # Also update the move validator's castling rights
    move_validator.castling_rights = castling_rights

def handle_promotion(piece_type):
    global promoting_pawn, turn
    
    if promoting_pawn:
        file, rank = promoting_pawn
        pawn_color = initial_board[rank][file][0]
        initial_board[rank][file] = pawn_color + piece_type
        promoting_pawn = None
        
        # Hoàn thành nước đi bằng cách đổi lượt
        turn = not turn

def move_piece(start_pos, end_pos):
    global castling_rights, turn, last_move, promoting_pawn
    save_state()
    history_stack.append({
        'board': copy.deepcopy(initial_board),
        'turn': turn,
        'castling_rights': castling_rights,
        'last_move': last_move
    })

    start_file, start_rank = start_pos
    end_file, end_rank = end_pos
    piece_moved = initial_board[start_rank][start_file]
    captured_piece = initial_board[end_rank][end_file]  # ← Lưu lại quân bị ăn (nếu có)

    # Kiểm tra bắt tốt qua đường
    if piece_moved[1] == 'P' and start_file != end_file and initial_board[end_rank][end_file] == '':
        if last_move:
            last_start, last_end = last_move
            last_start_file, last_start_rank = last_start
            last_end_file, last_end_rank = last_end

            # Xác định quân tốt bị bắt
            last_piece = initial_board[last_end_rank][last_end_file] if 0 <= last_end_rank < 8 and 0 <= last_end_file < 8 else ''
            if last_piece == ('bP' if piece_moved[0] == 'w' else 'wP'):
                if last_start_rank == (6 if piece_moved[0] == 'b' else 1) and last_end_rank == (4 if piece_moved[0] == 'b' else 3):
                    if last_end_file == end_file and last_end_rank == start_rank:
                        # Xóa quân tốt bị bắt
                        initial_board[last_end_rank][last_end_file] = ''
                        captured_piece = last_piece  # ← Ghi nhận quân bị bắt qua đường

    # Thực hiện di chuyển quân cờ
    initial_board[end_rank][end_file] = piece_moved
    initial_board[start_rank][start_file] = ''

    # Tốt phong cấp
    if piece_moved[1] == 'P' and (end_rank == 0 or end_rank == 7):
        promoting_pawn = (end_file, end_rank)
        return

    # Cập nhật nước đi cuối cùng
    last_move = (start_pos, end_pos)

    # Cập nhật quyền nhập thành
    update_castling_rights(piece_moved, start_pos)

    # Cập nhật validator
    move_validator.board = initial_board
    move_validator.castling_rights = castling_rights
    move_validator.last_move = last_move

    # Xử lý nhập thành (di chuyển xe)
    if piece_moved[1] == 'K' and abs(start_file - end_file) == 2:
        if end_file > start_file:  # Nhập thành cánh vua
            initial_board[end_rank][5] = initial_board[end_rank][7]
            initial_board[end_rank][7] = ''
            if piece_moved[0] == 'w':
                castling_rights = castling_rights.replace('K', '').replace('Q', '')
            else:
                castling_rights = castling_rights.replace('k', '').replace('q', '')
        else:  # Nhập thành cánh hậu
            initial_board[end_rank][3] = initial_board[end_rank][0]
            initial_board[end_rank][0] = ''
            if piece_moved[0] == 'w':
                castling_rights = castling_rights.replace('K', '').replace('Q', '')
            else:
                castling_rights = castling_rights.replace('k', '').replace('q', '')

    # Cập nhật lại validator
    move_validator.board = initial_board
    move_validator.castling_rights = castling_rights
    move_validator.last_move = last_move

def draw_promotion_menu(pawn_color):
    promotion_color = 'white' if pawn_color == 'w' else 'black'
    menu_width = SQUARE_SIZE
    menu_height = 4 * SQUARE_SIZE
    menu_x = WIDTH // 2 - menu_width // 2
    menu_y = HEIGHT // 2 - menu_height // 2
    
    # Vẽ nền menu
    pygame.draw.rect(win, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(win, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height), 2)
    
    # Vẽ các lựa chọn phong cấp
    for i, piece in enumerate(promotion_pieces):
        piece_key = f"{promotion_color}_{piece}"
        if piece_key in pieces:
            win.blit(pieces[piece_key], (menu_x, menu_y + i * SQUARE_SIZE))

def undo_move():
    global initial_board, turn, castling_rights, last_move, promoting_pawn

    if not history_stack:
        print("No move to undo.")
        return

    prev_state = history_stack.pop()
    initial_board = copy.deepcopy(prev_state['board'])
    turn = prev_state['turn']
    castling_rights = prev_state['castling_rights']
    last_move = prev_state['last_move']
    promoting_pawn = None

    # Cập nhật lại move validator
    move_validator.board = initial_board
    move_validator.castling_rights = castling_rights
    move_validator.last_move = last_move


# Main function
def draw_mode_selection():
    win.fill((30, 30, 30))
    title_font = pygame.font.SysFont("Arial", 48)
    option_font = pygame.font.SysFont("Arial", 36)

    title = title_font.render("Play Mode:", True, (255, 255, 255))
    pvp = option_font.render("PvP", True, (255, 255, 255))
    pve = option_font.render("PvE", True, (255, 255, 255))

    # Vị trí các nút bấm
    pvp_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 30, 300, 50)
    pve_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 40, 300, 50)

    running = True
    while running:
        win.fill((30, 30, 30))
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))

        # Vẽ nút PvP
        pygame.draw.rect(win, (70, 130, 180), pvp_rect)
        win.blit(pvp, (pvp_rect.x + (pvp_rect.width - pvp.get_width()) // 2,
                       pvp_rect.y + (pvp_rect.height - pvp.get_height()) // 2))

        # Vẽ nút PvE
        pygame.draw.rect(win, (70, 130, 180), pve_rect)
        win.blit(pve, (pve_rect.x + (pve_rect.width - pve.get_width()) // 2,
                       pve_rect.y + (pve_rect.height - pve.get_height()) // 2))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pvp_rect.collidepoint(event.pos):
                    return 'PvP'
                elif pve_rect.collidepoint(event.pos):
                    return 'PvE'

def save_state():
    history_stack.append({
        'board': copy.deepcopy(initial_board),
        'turn': turn,
        'castling_rights': castling_rights,
        'last_move': last_move
    })
    redo_stack.clear()

def undo_move():
    global initial_board, turn, castling_rights, last_move, promoting_pawn
    if not history_stack:
        return
    redo_stack.append({
        'board': copy.deepcopy(initial_board),
        'turn': turn,
        'castling_rights': castling_rights,
        'last_move': last_move
    })
    prev = history_stack.pop()
    initial_board[:] = copy.deepcopy(prev['board'])
    turn = prev['turn']
    castling_rights = prev['castling_rights']
    last_move = prev['last_move']
    promoting_pawn = None
    move_validator.board = initial_board
    move_validator.castling_rights = castling_rights
    move_validator.last_move = last_move

def redo_move():
    global initial_board, turn, castling_rights, last_move, promoting_pawn
    if not redo_stack:
        return
    save_state()
    state = redo_stack.pop()
    initial_board[:] = copy.deepcopy(state['board'])
    turn = state['turn']
    castling_rights = state['castling_rights']
    last_move = state['last_move']
    promoting_pawn = None
    move_validator.board = initial_board
    move_validator.castling_rights = castling_rights
    move_validator.last_move = last_move

def main():
    global selected_piece, selected_pos, turn, valid_moves, promoting_pawn, initial_board, game_over, winner, last_move, bot_thinking
    global game_mode, bot

    game_mode = draw_mode_selection()
    if game_mode == 'PvE':
        bot = ChessBot()
    else:
        bot = None

    last_move = None
    
    running = True
    clock = pygame.time.Clock()

    while running:
        # Kiểm tra trạng thái game
        current_color = 'w' if turn else 'b'
        if move_validator.is_checkmate(current_color):
            game_over = True
            winner = 'b' if current_color == 'w' else 'w'
        elif move_validator.is_stalemate(current_color):
            game_over = True
            winner = None

        if game_over:
            draw_board()
            display_game_result(winner)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    running = False
            continue

        # Bot đi nếu đến lượt đen trong chế độ PvE
        if game_mode == 'PvE' and not turn and not promoting_pawn and not game_over and not bot_thinking:
            print("[DEBUG] Launching bot thread...")
            bot_thinking = True

            def bot_thread():
                global last_move, promoting_pawn, turn, bot_thinking
                print("[DEBUG] Bot is thinking...")
                board_wrapper = BoardWrapper(initial_board, castling_rights, turn, last_move)
                result = bot.make_move(board_wrapper)

                if result:
                    start_idx, end_idx = result[0], result[1]
                    if isinstance(start_idx, int):
                        start_file, start_rank = start_idx % 8, start_idx // 8
                    else:
                        start_file, start_rank = start_idx

                    if isinstance(end_idx, int):
                        end_file, end_rank = end_idx % 8, end_idx // 8
                    else:
                        end_file, end_rank = end_idx
                    move_piece((start_file, start_rank), (end_file, end_rank))

                    # Xử lý bắt tốt qua đường
                    if bot.en_passant_capture:
                        ep_x, ep_y = bot.en_passant_capture
                        initial_board[ep_y][ep_x] = ''
                        bot.en_passant_capture = None

                    # Kiểm tra phong cấp cho bot
                    piece = initial_board[end_rank][end_file]
                    if piece[1] == 'P' and (end_rank == 0 or end_rank == 7):
                        initial_board[end_rank][end_file] = piece[0] + 'Q'  # Bot tự động phong cấp thành hậu
                        promoting_pawn = None
                        turn = not turn
                    else:
                        turn = not turn

                    last_move = ((start_file, start_rank), (end_file, end_rank))
                    move_validator.board = initial_board
                    move_validator.last_move = last_move
                    print("[DEBUG] Bot has moved.")

                bot_thinking = False

            threading.Thread(target=bot_thread).start()

        # Xử lý sự kiện người chơi
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    undo_move()

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                mouse_pos = pygame.mouse.get_pos()
                file, rank = get_square_at_pos(mouse_pos)

                # Xử lý phong cấp
                if promoting_pawn:
                    pawn_file, pawn_rank = promoting_pawn
                    menu_width = SQUARE_SIZE
                    menu_height = 4 * SQUARE_SIZE
                    menu_x = WIDTH // 2 - menu_width // 2
                    menu_y = HEIGHT // 2 - menu_height // 2
                    
                    if (menu_x <= mouse_pos[0] < menu_x + menu_width and 
                        menu_y <= mouse_pos[1] < menu_y + menu_height):
                        selected_index = (mouse_pos[1] - menu_y) // SQUARE_SIZE
                        if 0 <= selected_index < len(promotion_pieces):
                            handle_promotion(promotion_pieces[selected_index])
                    continue

                # Xử lý chọn quân và di chuyển
                piece_code = initial_board[rank][file]
                
                if selected_piece is None:
                    # Trong PvE, người chơi chỉ được chọn quân trắng khi đến lượt trắng
                    if (game_mode == 'PvP' and piece_code and ((turn and piece_code[0] == 'w') or (not turn and piece_code[0] == 'b'))) or \
                       (game_mode == 'PvE' and turn and piece_code and piece_code[0] == 'w'):
                        selected_piece = piece_code
                        selected_pos = (file, rank)
                        valid_moves = move_validator.get_all_valid_moves(selected_pos)
                else:
                    if (file, rank) in valid_moves:
                        move_piece(selected_pos, (file, rank))
                        if not promoting_pawn:
                            turn = not turn
                    selected_piece = None
                    selected_pos = None
                    valid_moves = []

        # Vẽ bàn cờ
        draw_board()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()