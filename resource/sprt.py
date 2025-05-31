import chess
import chess.engine
import random
from evaluation import Evaluation
from move_validator import MoveValidator
from bot import ChessBot

# ✅ Đường dẫn đến Stockfish
stockfish_path = r"D:\Chess_Test\stockfish\stockfish-windows-x86-64-avx2.exe"
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1320})

MAX_GAMES = 10
MOVE_TIME = 0.25  # giây cho mỗi nước
wins, draws, losses = 0, 0, 0

def run_game(play_white_as_bot):
    global wins, draws, losses

    board = chess.Board()
    validator = MoveValidator([[''] * 8 for _ in range(8)], "KQkq")
    bot = ChessBot(validator)
    bot_color = chess.WHITE if play_white_as_bot else chess.BLACK

    while not board.is_game_over():
        if board.turn == bot_color:
            board_array = []
            for rank in range(7, -1, -1):  # từ hàng 8 đến 1
                row = []
                for file in range(8):  # từ cột a đến h
                    piece = board.piece_at(chess.square(file, rank))
                    if piece:
                        color = 'w' if piece.color == chess.WHITE else 'b'
                        row.append(color + piece.symbol().upper())
                    else:
                        row.append('')
                board_array.append(row)

            validator.board = board_array
            validator.last_move = bot.last_move
            bot.make_move(board_array, board.turn == chess.WHITE, board.castling_xfen(), bot.last_move)
            move = bot.last_move

            if move:
                start, end = move
                from_square = chess.square(start[0], 7 - start[1])
                to_square = chess.square(end[0], 7 - end[1])
                chess_move = chess.Move(from_square, to_square)

                if chess_move in board.legal_moves:
                    board.push(chess_move)
                else:
                    print(f"[ERROR] Illegal move attempted: {chess_move}")
                    break
            else:
                break
        else:
            result = engine.play(board, chess.engine.Limit(time=MOVE_TIME))
            board.push(result.move)

    result = board.result()
    if result == "1-0":
        if play_white_as_bot:
            wins += 1
        else:
            losses += 1
    elif result == "0-1":
        if play_white_as_bot:
            losses += 1
        else:
            wins += 1
    else:
        draws += 1

# 🔁 Vòng lặp SPRT chính
for game_number in range(1, MAX_GAMES + 1):
    run_game(play_white_as_bot=(game_number % 2 == 1))
    print(f"Game {game_number:03}: W {wins} | D {draws} | L {losses}")

print("\n=== SPRT Test Completed ===")
print(f"✅ Total Wins:   {wins}")
print(f"🤝 Total Draws:  {draws}")
print(f"❌ Total Losses: {losses}")

engine.quit()
