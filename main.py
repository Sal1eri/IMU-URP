import os
import time
import hashlib
import requests
from html.parser import HTMLParser
from urllib.parse import urljoin
# ================== 配置区 ==================
URP_BASE_URL = "https://jwxt.imu.edu.cn"
LOGIN_URL = f"{URP_BASE_URL}/login"

# Write your student ID and password here.
STUDENT_ID = os.getenv("STUDENT_ID", "请输入学号")
PASSWORD = os.getenv("PASSWORD", "请输入密码")

TIMEOUT = 15
VERIFY_TLS = True

CAPTCHA_SAVE_PATH = "captcha.jpg"
URP_SUFFIX = "{Urp602019}"
# ===========================================


class LoginPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.found_form = False
        self.form_action = None
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag.lower() == "form" and not self.found_form:
            self.in_form = True
            self.found_form = True
            self.form_action = attrs.get("action", "")

        if tag.lower() == "input" and self.in_form:
            name = attrs.get("name")
            if name:
                self.inputs[name] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag.lower() == "form":
            self.in_form = False


# ======= 加密部分 =======

def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest().lower()


def build_j_password(password: str) -> str:
    """
    对应页面 onclick:

    hex_md5(hex_md5(p), '1.8') + '*' + hex_md5(hex_md5(p, '1.8'), '1.8')

    规则来源 md5.min.js:
    - hex_md5(x)            -> md5(x + "{Urp602019}")
    - hex_md5(x, '1.8')     -> md5(x)
    """

    # hex_md5(p) -> md5(p + suffix)
    inner_left = md5_hex(password + URP_SUFFIX)
    part_left = md5_hex(inner_left)

    # hex_md5(p, '1.8') -> md5(p)
    inner_right = md5_hex(password)
    part_right = md5_hex(inner_right)

    return f"{part_left}*{part_right}"


# ======= 登录流程 =======

def fetch_login_page(session):
    r = session.get(LOGIN_URL, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()
    if r.encoding is None or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding
    return r.url, r.text


def parse_login_page(page_url, html_text):
    parser = LoginPageParser()
    parser.feed(html_text)

    if not parser.found_form:
        raise RuntimeError("未找到登录表单")

    action_url = urljoin(page_url, parser.form_action or "")
    captcha_url = urljoin(page_url, "/img/captcha.jpg")

    return action_url, parser.inputs, captcha_url


def download_captcha(session, captcha_url):
    captcha_url = f"{captcha_url}?{int(time.time() * 1000)}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": LOGIN_URL,
    }

    r = session.get(captcha_url, headers=headers, timeout=TIMEOUT, verify=VERIFY_TLS)
    r.raise_for_status()

    if "image" not in (r.headers.get("Content-Type", "").lower()):
        raise RuntimeError("验证码响应不是图片")

    with open(CAPTCHA_SAVE_PATH, "wb") as f:
        f.write(r.content)

    print(f"验证码已保存到: {os.path.abspath(CAPTCHA_SAVE_PATH)}")


def login(session):
    page_url, html_text = fetch_login_page(session)
    action_url, inputs, captcha_url = parse_login_page(page_url, html_text)

    download_captcha(session, captcha_url)
    captcha_value = input("请输入验证码: ").strip()

    payload = dict(inputs)
    payload["j_username"] = STUDENT_ID
    payload["j_password"] = build_j_password(PASSWORD)
    payload["j_captcha"] = captcha_value

    print("computed j_password:", payload["j_password"])

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": URP_BASE_URL,
        "Referer": LOGIN_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = session.post(
        action_url,
        data=payload,
        headers=headers,
        timeout=TIMEOUT,
        verify=VERIFY_TLS,
        allow_redirects=True,
    )

    return resp


def login_success(resp: requests.Response) -> bool:
    if "errorCode=" in resp.url:
        return False
    if "j_spring_security_check" in (resp.text or ""):
        return False
    return True


def fetch_index(session):
    r = session.get(URP_BASE_URL + "/", timeout=TIMEOUT, verify=VERIFY_TLS)
    r.encoding = r.apparent_encoding

    print("\n===== 首页检测 =====")
    print("index URL:", r.url)
    print("index status:", r.status_code)
    print("是否像登录页:", "j_spring_security_check" in r.text)

    return r




# 后续可以在这里实现选课等功能，使用 session 进行认证后的请求
def registration4classes(session):
    # 这里可以实现后续的选课流程，使用 session 进行认证后的请求
    # 例如：
    # 1. 获取选课页面，解析课程列表
    # 2. 提交选课请求
    # 3. 处理选课结果
    # 具体实现会根据选课系统的接口和流程来编写
    pass
# 可以根据需要添加更多功能，比如查询成绩、课表等


def parse_captcha_solution():
    # 这里可以实现验证码识别的逻辑，例如使用 OCR 库来自动识别验证码
    # 目前先留空，等待用户手动输入验证码
    pass


# ======= 主程序 =======

if __name__ == "__main__":
     with requests.Session() as s:
        resp = login(s)
        print(s.__dict__)
        print("\n===== 登录结果 =====")
        print("最终URL:", resp.url)
        print("状态码:", resp.status_code)
        print("cookies:", s.cookies.get_dict())
        print("登录成功:", login_success(resp))

        fetch_index(s)