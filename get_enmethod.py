import requests

LOGIN_URL = "https://jwxt.imu.edu.cn/login"
TIMEOUT = 15
VERIFY_TLS = True

KEYS = ["hex_md5", "j_password", "tokenValue", "sm3", "j_username", "j_captcha", "*"]

def dump_context(text: str, key: str, window: int = 400, max_hits: int = 10):
    low = text.lower()
    key_low = key.lower()
    idx = 0
    hits = 0
    while True:
        pos = low.find(key_low, idx)
        if pos == -1 or hits >= max_hits:
            break
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        snippet = text[start:end]
        print(f"\n=== HIT key={key} at {pos} ===")
        print(snippet)
        idx = pos + len(key_low)
        hits += 1

def main():
    s = requests.Session()
    r = s.get(LOGIN_URL, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    if r.encoding is None or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding
    html = r.text

    print("len(html) =", len(html))

    for k in KEYS:
        dump_context(html, k, window=500, max_hits=6)

if __name__ == "__main__":
    main()