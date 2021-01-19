import base64
import hashlib
import hmac
import time
import urllib
import requests
import json


class DingTalkNotify:
    def __init__(self):
        self._url = "https://oapi.dingtalk.com/robot/send?access_token=57ab163a3c5dddbefa68141a5c8987b7a1fd1a68daff89722f9dee485c4341da"
        self._secret = "SEC4d6f2c996c44b28da41b45d7a4244be4ef9385344d61fc518d2c26a1d4858bc0"

    def send_msg(self, msg):
        timestamp = str(round(time.time() * 1000))
        sign = self.sign(timestamp, self._secret)
        body = {"msgtype": "text", "text": {"content": "" + msg + ""}}
        url = self._url + "&timestamp=" + timestamp + "&sign=" + sign
        body = json.dumps(body)
        headers = {'content-type': 'application/json;charset=utf-8'}
        resp = requests.post(url, headers=headers, data=body)

    def sign(self, timestamp, secret):
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
#
#
def main():
    msg = str.format(
        "short time buy1 wave over size:{0:.5f},price diff:{1:.2f}, now time:{2}, current_buy1:{3}, time_diff:{4:.2f}, timeDiff:{5:.2f}",
        1, 2, 3, 4, 2, 1)
    # dd = DingTalkNotify()
    # dd.send_msg(msg)
    print(msg)


if __name__ == '__main__':
    main()
