import os
import re
import json
import random
import time
import hashlib
import requests
from html.parser import HTMLParser
from urllib.parse import urljoin
from dotenv import load_dotenv
from captcha_ocr import recognize_captcha

load_dotenv()

C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_RESET = "\033[0m"

def info(msg):
    print(f"{C_CYAN}[*]{C_RESET} {msg}")

def ok(msg):
    print(f"{C_GREEN}[OK]{C_RESET} {msg}")

def fail(msg):
    print(f"{C_RED}[FAIL]{C_RESET} {msg}")

def warn(msg):
    print(f"{C_YELLOW}[!]{C_RESET} {msg}")
# ================== 配置区 ==================
URP_BASE_URL = os.getenv("URP_BASE_URL")
if not URP_BASE_URL:
    print(f"{C_RED}[FAIL]{C_RESET} 请在 .env 中设置 URP_BASE_URL")
    exit(1)
LOGIN_URL = f"{URP_BASE_URL}/login"

STUDENT_ID = os.getenv("STUDENT_ID")
if not STUDENT_ID:
    print(f"{C_RED}[FAIL]{C_RESET} 请在 .env 中设置 STUDENT_ID")
    exit(1)

PASSWORD = os.getenv("PASSWORD")
if not PASSWORD:
    print(f"{C_RED}[FAIL]{C_RESET} 请在 .env 中设置 PASSWORD")
    exit(1)

TIMEOUT = int(os.getenv("TIMEOUT", "15"))
VERIFY_TLS = os.getenv("VERIFY_TLS", "true").lower() == "true"
CAPTCHA_SAVE_PATH = os.getenv("CAPTCHA_SAVE_PATH", "captcha.jpg")
URP_SUFFIX = os.getenv("URP_SUFFIX", "{Urp602019}")
MAX_OCR_RETRIES = int(os.getenv("MAX_OCR_RETRIES", "3"))
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

    return r.content


def login(session, max_ocr_retries=None):
    if max_ocr_retries is None:
        max_ocr_retries = MAX_OCR_RETRIES
    j_password = build_j_password(PASSWORD)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": URP_BASE_URL,
        "Referer": LOGIN_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for attempt in range(1, max_ocr_retries + 1):
        info(f"第 {attempt} 次尝试")
        info("获取登录页面...")
        page_url, html_text = fetch_login_page(session)
        action_url, inputs, captcha_url = parse_login_page(page_url, html_text)

        info("下载验证码...")
        image_bytes = download_captcha(session, captcha_url)
        info("识别验证码...")
        captcha_value = recognize_captcha(image_bytes)
        info(f"识别结果: {captcha_value}")

        payload = dict(inputs)
        payload["j_username"] = STUDENT_ID
        payload["j_password"] = j_password
        payload["j_captcha"] = captcha_value

        info("提交登录...")
        resp = session.post(
            action_url,
            data=payload,
            headers=headers,
            timeout=TIMEOUT,
            verify=VERIFY_TLS,
            allow_redirects=True,
        )

        if login_success(resp):
            return resp

        fail(f"登录失败")

    warn(f"OCR 识别失败次数过多")
    info("手动输入")
    info("获取登录页面...")
    page_url, html_text = fetch_login_page(session)
    action_url, inputs, captcha_url = parse_login_page(page_url, html_text)

    info("下载验证码...")
    image_bytes = download_captcha(session, captcha_url)
    with open(CAPTCHA_SAVE_PATH, "wb") as f:
        f.write(image_bytes)
    info(f"验证码已保存到: {os.path.abspath(CAPTCHA_SAVE_PATH)}")
    captcha_value = input(f"{C_YELLOW}[?]{C_RESET} 请输入验证码: ").strip()

    payload = dict(inputs)
    payload["j_username"] = STUDENT_ID
    payload["j_password"] = j_password
    payload["j_captcha"] = captcha_value

    info("提交登录...")
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
    info("访问首页...")
    r = session.get(URP_BASE_URL + "/", timeout=TIMEOUT, verify=VERIFY_TLS)
    r.encoding = r.apparent_encoding

    is_login_page = "j_spring_security_check" in r.text
    info(f"首页: {r.url} (状态: {r.status_code})")
    if is_login_page:
        warn("当前仍在登录页面")

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


def _wcswidth(s: str) -> int:
    return sum(2 if ord(ch) > 127 else 1 for ch in s)

def _pad(s: str, width: int) -> str:
    s = "" if s is None else str(s)
    return s + " " * max(0, width - _wcswidth(s))

def _boxw(n: int) -> str:
    return "─" * n


# ======= 成绩查询 =======

def fetch_and_print_scores(session):
    info("获取成绩页面...")
    r = session.get("https://jwxt.imu.edu.cn/student/integratedQuery/scoreQuery/allTermScores/index", timeout=TIMEOUT, verify=VERIFY_TLS)
    r.encoding = r.apparent_encoding

    m = re.search(r'var\s+url\s*=\s*["\']([^"\']+)["\']', r.text)
    if not m:
        fail("未找到成绩数据接口")
        return

    search_url = m.group(1)
    resp = session.post(
        urljoin("https://jwxt.imu.edu.cn", search_url),
        data={"pageNum": 1, "pageSize": 200},
        timeout=TIMEOUT,
        verify=VERIFY_TLS,
    )

    if resp.status_code != 200:
        fail("获取成绩数据失败")
        return

    data = resp.json()
    records = data.get("list", {}).get("records", [])
    if not records:
        warn("没有找到成绩记录")
        return

    semesters = {}
    graded_credits = 0
    graded_weighted = 0
    graded_count = 0
    passfail_courses = []

    for r in records:
        sem_name = r.get("ZXJXJHM", "未知学期")
        course_name = r.get("KCM", "未知课程")
        credits = float(r.get("XF", 0))
        try:
            score = float(r.get("KCCJ"))
        except (ValueError, TypeError):
            continue

        if score < 0 or score == 0:
            continue

        is_pf = (score == 64)
        semesters.setdefault(sem_name, []).append((course_name, credits, score, is_pf))

        if is_pf:
            passfail_courses.append((course_name, credits, score))
        else:
            graded_credits += credits
            graded_weighted += credits * score
            graded_count += 1

    total_credits = graded_credits + sum(c for _, c, _ in passfail_courses)

    def score_color(s):
        if s >= 90: return C_GREEN
        if s >= 80: return C_CYAN
        if s >= 70: return C_YELLOW
        return C_RED

    cols = ["课程", "学分", "成绩"]
    colw = {c: _wcswidth(c) for c in cols}
    for items in semesters.values():
        for cn, cr, sc, is_pf in items:
            colw["课程"] = max(colw["课程"], _wcswidth(cn))
            colw["学分"] = max(colw["学分"], _wcswidth(f"{cr:.1f}"))
            sc_str = "合格" if is_pf else (f"{sc:.1f}" if isinstance(sc, float) and sc != int(sc) else f"{int(sc)}")
            colw["成绩"] = max(colw["成绩"], _wcswidth(sc_str))

    def hrule(a, b, c):
        return a + "+".join("-" * (colw[x] + 2) for x in cols) + c

    print()
    for sem_name in semesters:
        courses = semesters[sem_name]
        print(f"  [{sem_name}]")
        print(f"  {hrule('.', '.', '.')}")
        print(f"  |{'|'.join(f' {_pad(c, colw[c])} ' for c in cols)}|")
        print(f"  {hrule('+', '+', '+')}")
        for cn, cr, sc, is_pf in courses:
            cn_pad = _pad(cn, colw["课程"])
            cr_pad = _pad(f"{cr:.1f}", colw["学分"])
            if is_pf:
                sc_pad = _pad("合格", colw["成绩"])
                sc_disp = f"{C_YELLOW}{sc_pad}{C_RESET}"
            else:
                sc_str = f"{sc:.1f}" if isinstance(sc, float) and sc != int(sc) else f"{int(sc)}"
                sc_pad = _pad(sc_str, colw["成绩"])
                sc_disp = f"{score_color(sc)}{sc_pad}{C_RESET}"
            print(f"  | {cn_pad} | {cr_pad} | {sc_disp} |")
        print(f"  {hrule(chr(39), chr(39), chr(39))}")
        print()

    avg = graded_weighted / graded_credits if graded_credits > 0 else 0

    def score_to_gpa(s):
        if s >= 90: return 4.0
        if s >= 85: return 3.7
        if s >= 82: return 3.3
        if s >= 78: return 3.0
        if s >= 75: return 2.7
        if s >= 72: return 2.3
        if s >= 68: return 2.0
        if s >= 64: return 1.5
        if s >= 60: return 1.0
        return 0

    gpa = 0
    if graded_credits > 0:
        gpa_sum = 0
        for items in semesters.values():
            for cn, cr, sc, is_pf in items:
                if not is_pf:
                    gpa_sum += score_to_gpa(sc) * cr
        gpa = gpa_sum / graded_credits

    l1 = f"  总学分: {total_credits:.0f}  课程数: {graded_count + len(passfail_courses)}  "
    l2 = f"  加权平均分: {avg:.2f}  |  GPA: {gpa:.2f}  "
    w1, w2 = _wcswidth(l1), _wcswidth(l2)
    w = max(w1, w2)
    n = w + 2
    print(f"  .{'-' * n}.")
    print(f"  | {_pad(l1, w)} |")
    print(f"  | {_pad(l2, w)} |")
    print(f"  '{'-' * n}'")

    trivia = [
        "章鱼有三颗心脏。",
        "香蕉其实是浆果，草莓不是。",
        "北极熊的皮肤是黑色的，毛是透明的。",
        "人的胃酸可以溶解刀片，但需要几天时间。",
        "树懒一周只排便一次。",
        "猫的呼噜声频率有助于骨骼恢复。",
        "袋鼠不会向后走。",
        "水母没有大脑也没有心脏。",
        "鸵鸟的眼睛比它的大脑大。",
        "蜂蜜永远不会变质。",
        "人类和香蕉共享约 60% 的 DNA。",
        "每天约 100 颗陨石落到地球，多数落入海洋。",
        "打喷嚏时心脏会短暂停跳。",
        "胃每 3 天换一层内膜，防止被自己消化。",
        "蓝色是自然界中最稀少的颜色之一。",
        "大象是唯一不会跳的哺乳动物。",
        "成年人每天脱落约 50-100 根头发。",
        "火星上的日落是蓝色的。",
        "你体内的细菌比人体细胞还多。",
        "长颈鹿的舌头可以舔到自己的耳朵内部。",
    ]

    if random.random() < 0.7:
        try:
            loc = requests.get("http://ip-api.com/json/", timeout=5).json()
            city = loc.get("city", "")
            if city:
                w = requests.get(f"https://wttr.in/{city}?format=%C+%t+%w+%h", timeout=5)
                w.encoding = "utf-8"
                parts = w.text.strip().split()
                if len(parts) >= 4:
                    cond_parts = []
                    i = 0
                    while i < len(parts) and not parts[i].endswith("°C"):
                        cond_parts.append(parts[i])
                        i += 1
                    cond = " ".join(cond_parts)
                    temp = parts[i]
                    wind = parts[i + 1] if i + 1 < len(parts) else ""
                    hum = parts[i + 2] if i + 2 < len(parts) else ""
                    temp_num = int(temp.replace("°C", "")) if "°C" in temp else 20
                    msg = f"{city} {cond} {temp} 湿度{hum} 风速{wind}"
                    if "rain" in cond.lower() or "drizzle" in cond.lower() or "shower" in cond.lower():
                        msg += "，出门记得带伞 ☔"
                    elif "snow" in cond.lower() or "sleet" in cond.lower() or "blizzard" in cond.lower():
                        msg += "，注意保暖 ❄️"
                    elif temp_num >= 35:
                        msg += "，注意防暑 🥵"
                    elif temp_num <= 5:
                        msg += "，多穿点别感冒 🧣"
                    elif "sun" in cond.lower() or "clear" in cond.lower():
                        msg += "，好天气！适合出去走走 🌞"
                    elif "cloud" in cond.lower() or "overcast" in cond.lower() or "mist" in cond.lower():
                        msg += "，今天没有太阳，心情也要晴朗哦"
                    print(f"  {C_CYAN}🌤{C_RESET} {msg}")
                else:
                    print(f"  {C_CYAN}💬{C_RESET} {random.choice(trivia)}")
            else:
                print(f"  {C_CYAN}💬{C_RESET} {random.choice(trivia)}")
        except Exception:
            print(f"  {C_CYAN}💬{C_RESET} {random.choice(trivia)}")
    else:
        print(f"  {C_CYAN}💬{C_RESET} {random.choice(trivia)}")


# ======= 主程序 =======

if __name__ == "__main__":
    with requests.Session() as s:
        info("正在登录 URP 系统...")
        resp = login(s)

        if login_success(resp):
            ok("登录成功")
            fetch_and_print_scores(s)
        else:
            fail("登录失败")
            info(f"URL: {resp.url}")

        fetch_index(s)