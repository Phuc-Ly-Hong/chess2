import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chess
import chess.engine
import random
import math
from engine.bot import ChessBot
from core.move_validator import MoveValidator
from core.board_wrapper import BoardWrapper

stockfish_path = r"D:\Chess_Test\stockfish\stockfish-windows-x86-64-avx2.exe"
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1320})

MAX_GAMES = 10
MOVE_TIME = 6.0
wins, draws, losses = 0, 0, 0

def convert_last_move_for_book(last_move):
    if last_move and isinstance(last_move, tuple) and all(isinstance(x, int) for x in last_move):
        start, end = last_move
        return ((start % 8, 7 - (start // 8)), (end % 8, 7 - (end // 8)))
    elif last_move and isinstance(last_move, tuple) and len(last_move) == 2 and all(isinstance(x, tuple) for x in last_move):
        return last_move
    return None

def run_game(play_white_as_bot):
    global wins, draws, losses
    board = chess.Board()
    validator = MoveValidator([[''] * 8 for _ in range(8)], "KQkq")
    bot = ChessBot()
    bot_color = chess.WHITE if play_white_as_bot else chess.BLACK

    while not board.is_game_over():
        if board.turn == bot_color:
            board_array = []
            for rank in range(7, -1, -1):
                row = []
                for file in range(8):
                    piece = board.piece_at(chess.square(file, rank))
                    if piece:
                        color = 'w' if piece.color == chess.WHITE else 'b'
                        row.append(color + piece.symbol().upper())
                    else:
                        row.append('')
                board_array.append(row)

            wrapper = BoardWrapper(
                board_array,
                board.castling_xfen(),
                'w' if board.turn == chess.WHITE else 'b',
                convert_last_move_for_book(bot.last_move)
            )

            move = bot.make_move(wrapper)

            if move:
                if len(move) == 2 and all(isinstance(x, int) for x in move):
                    start, target = move
                    start_file, start_rank = start % 8, 7 - (start // 8)
                    target_file, target_rank = target % 8, 7 - (target // 8)
                elif len(move) == 2 and all(isinstance(x, tuple) for x in move):
                    start_file, start_rank = move[0]
                    target_file, target_rank = move[1]
                else:
                    print(f"[ERROR] Invalid move format: {move}")
                    bot.use_opening_book = False
                    continue

                from_sq = chess.square(start_file, start_rank)
                to_sq = chess.square(target_file, target_rank)
                chess_move = chess.Move(from_sq, to_sq)

                if chess_move in board.legal_moves:
                    board.push(chess_move)
                    bot.last_move = (from_sq, to_sq)
                else:
                    print(f"[ERROR] Illegal move attempted: {chess_move}. Skipping.")
                    bot.use_opening_book = False
                    continue
            else:
                print("[ERROR] Bot returned no move")
                break
        else:
            result = engine.play(board, chess.engine.Limit(time=MOVE_TIME))
            board.push(result.move)

    result = board.result()
    if result == "1-0":
        wins += 1 if play_white_as_bot else 0
        losses += 0 if play_white_as_bot else 1
    elif result == "0-1":
        losses += 1 if play_white_as_bot else 0
        wins += 0 if play_white_as_bot else 1
    else:
        draws += 1

# Main loop
for game_number in range(1, MAX_GAMES + 1):
    run_game(play_white_as_bot=(game_number % 2 == 1))
    print(f"Game {game_number:03}: W {wins} | D {draws} | L {losses}")

print("\n=== SPRT Test Completed ===")
print(f"✅ Total Wins:   {wins}")
print(f"🤝 Total Draws:  {draws}")
print(f"❌ Total Losses: {losses}")

total_games = wins + draws + losses
score = (wins + 0.5 * draws) / total_games
elo = -400 * (math.log10(1 / score - 1)) + 1320
print(f"\n📊 Estimated Bot Elo: {elo:.2f} (vs Stockfish 1320)")

engine.quit()
