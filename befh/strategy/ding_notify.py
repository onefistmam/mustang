import base64
import hashlib
import hmac
import time
import urllib


class DingTalkNotify:
    def __init__(self):
        pass

    def send_msg(self, url, msg):
        pass

    def sign(self, msg):
        timestamp = str(round(time.time() * 1000))
        secret_enc = msg.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, msg)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        print(timestamp)
        print(sign)
