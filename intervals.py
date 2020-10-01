import threading


class repeating:
    def __init__(self, interval_calculator):
        self.interval = interval_calculator

    def __call__(self, func):
        def wrapped(*args):
            func(*args)
            sleep_for = self.interval()
            threading.Timer(sleep_for, lambda: wrapped(*args)).start()
        return wrapped
