import queue
import threading
import concurrent.futures


class Pipeline(queue.Queue):
    def __init__(self):
        super().__init__(maxsize=10)

    def get_message(self):
        value = self.get()
        return value

    def set_message(self, value):
        self.put(value)


def producer(p, e):
    while not e.is_set():
        p.set_message(123)


def consumer(p, e):
    while not e.is_set() or not p.empty():
        message = p.get_message()


if __name__ == "__main__":
    pipeline = Pipeline()
    event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.submit(producer, pipeline, event)
        executor.submit(consumer, pipeline, event)
        event.set()
