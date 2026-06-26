import ddddocr

_ocr = ddddocr.DdddOcr(show_ad=False)

def recognize_captcha(image_bytes: bytes) -> str:
    return _ocr.classification(image_bytes)


if __name__ == "__main__":
    import requests
    import time
    from main import LOGIN_URL, TIMEOUT, VERIFY_TLS

    with requests.Session() as s:
        s.get(LOGIN_URL, timeout=TIMEOUT, verify=VERIFY_TLS)

        captcha_url = f"{LOGIN_URL}/../../../img/captcha.jpg?{int(time.time() * 1000)}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": LOGIN_URL}
        r = s.get(captcha_url, headers=headers, timeout=TIMEOUT, verify=VERIFY_TLS)
        r.raise_for_status()

        result = recognize_captcha(r.content)
        print(f"验证码识别结果: {result}")
