
class PairConverter:
    @staticmethod
    def convertPair(pair: str, exchange: str):
        if exchange.lower() == "binance" and "/" in pair:
            tmp_pair = pair.replace("/", "-")
            return tmp_pair
        return pair


