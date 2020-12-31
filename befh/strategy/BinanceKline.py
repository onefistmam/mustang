class BinanceKline:

    def __init__(self, open_p, close_p, start_t, end_t, high_P, low_p, finish):
        self._open_p = open_p
        self._close_p = close_p
        self._start_t = start_t
        self._end_t = end_t
        self._high_P = high_P
        self._low_p = low_p
        self._finish = finish


    @property
    def get_open_p(self):
        return self._open_p

    @property
    def finish(self):
        return self._finish
