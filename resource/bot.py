from searcher import Search
from board_wrapper import BoardWrapper
from opening_book import OpeningBook

class ChessBot:
    def __init__(self):
        self.searcher = Search()
        self.last_move = None
        self.en_passant_capture = None
        try:
            self.opening_book = OpeningBook(file_path=r"d:\Chess_Test\resource\Book.txt")  
        except Exception as e:
            print(f"[Bot] Failed to load opening book: {e}")
            self.opening_book = None

    def make_move(self, board_wrapper):
        print("[DEBUG] Bot.make_move(): bat dau goi search")

        board_array = board_wrapper.board_array
        turn = board_wrapper.is_white_to_move()
        castling_rights = board_wrapper.castling_rights
        last_move = board_wrapper.last_move

        move = None

        if self.opening_book:
            color = 'w' if turn else 'b'
            book_move = self.opening_book.try_get_book_move(
                board_array, color, turn, castling_rights, last_move
            )
            if book_move:
                move = book_move
                print(f"[DEBUG] Bot.make_move(): chon nuoc tu Opening Book: {move}")
                self.last_move = move

        if not move:
            move = self.searcher.search(board_wrapper, time_limit=7.0)
            self.last_move = move

        self.en_passant_capture = None
        if move:
            start, end = move[0], move[1]

            if isinstance(start, int):
                start = (start % 8, start // 8)
            if isinstance(end, int):
                end = (end % 8, end // 8)

            sf, sr = start
            ef, er = end

            piece = board_array[sr][sf]
            if piece and piece[1] == 'P' and sf != ef and board_array[er][ef] == '':
                self.en_passant_capture = (ef, sr)

        print(f"[DEBUG] Bot.make_move(): bot chon nuoc {move}")
        return move


        