import time

class TimeManager:
    def __init__(self, total_time=300.0, increment=2.0):
        self.total_time = total_time  # Tổng thời gian dành cho bot (giây)
        self.increment = increment    # Increment mỗi nước (giây)
        self.start_time = None
        self.moves_played = 0

    def start_timer(self):
        self.start_time = time.time()

    def time_elapsed(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def remaining_time(self):
        return self.total_time - self.time_elapsed()

    def choose_depth(self, board_array, phase):
        """
        Quyết định depth tìm kiếm dựa vào phase (early, mid, late)
        """
        move_count = sum(1 for rank in board_array for p in rank if p != '')
        
        # Số quân còn lại đánh giá phase
        if move_count > 24:
            phase = 'opening'
        elif move_count > 12:
            phase = 'middlegame'
        else:
            phase = 'endgame'

        # Điều chỉnh độ sâu tùy theo phase và thời gian
        if phase == 'opening':
            return 3
        elif phase == 'middlegame':
            return 4 if self.remaining_time() > 30 else 3
        else:
            return 5 if self.remaining_time() > 60 else 3
