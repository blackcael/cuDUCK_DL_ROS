from collections import deque


class RobustStopBuffer:
    def __init__(self, length=10):
        # Automatically discard oldest entries when full
        self.length = length
        self.queue = deque(maxlen=length)

    def append(self, item: bool):
        self.queue.append(item)

    def get_certainty(self):
        return sum(self.queue) / self.length

    def clear(self):
        self.queue.clear()

    def set_buffer_size(self, new_buffer_size):
        self.length = new_buffer_size
        self.queue = deque(maxlen = new_buffer_size)
