<p align="center">
  <h1 align="center">IMU-URP</h1>
  <p align="center">
    <a href="#-中文文档">🇨🇳 中文</a> •
    <a href="#-english">🇬🇧 English</a>
  </p>
</p>

---

## 🇨🇳 中文文档

教务系统自动登录 & 成绩查询脚本。

### 文件结构

```
IMU-URP/
├── main.py            # 主程序：登录、成绩查询、终端输出
├── captcha_ocr.py     # 验证码识别模块（ddddocr）
├── encryption.py      # 密码加密算法参考
├── get_enmethod.py    # 抓取登录页面，分析加密方法
├── .env               # 学号和密码配置（需手动编辑）
├── .env.example       # 配置模板
├── requirements.txt   # Python 依赖列表
└── README.md          # 本文件
```

### 使用

```bash
cp .env.example .env
# 编辑 .env 填入你的学号和密码及 URP 地址
pip install -r requirements.txt
python main.py
```

首次运行会自动下载 ddddocr 的模型文件（约 10MB）。

### 功能

| 功能                     | 状态     |
|--------------------------|----------|
| 自动验证码识别           | ✅       |
| 自动登录                 | ✅       |
| 全部学期成绩查询         | ✅       |
| 按学期分组展示           | ✅       |
| 加权平均分计算           | ✅       |
| GPA 估算                   | ✅       |
| 排除合格制课程           | ✅       |
| 彩色终端输出             | ✅       |
| 手动输入验证码回退       | ✅       |
| 选课功能                 | ⬜ 待实现 |

### 运行示例

```
[*] 第 1 次尝试
[*] 获取登录页面...
[*] 下载验证码...
[*] 识别验证码...
[*] 识别结果: n5c2
[*] 提交登录...
[OK] 登录成功

[2021-2022学年秋]
.------------------------------------------+------+------+------.
| 课程                                     | 学分 | 成绩 | GPA  |
+------------------------------------------+------+------+------+
| 课程 A                                    | 6.0  | 95   | 4.0  |
| 课程 B                                    | 6.0  | 80   | 3.0  |
| 课程 C                                    | 3.0  | 93   | 4.0  |
| ...                                       | ...  | ...  | ...  |
'------------------------------------------+------+------+------'

.-------------------------------------.
|  总学分: 180  课程数: 60           |
|  加权平均分: 85.00  |  GPA: 3.50   |
'-------------------------------------'
[OK] 成绩良好 (含合格制课程不参与 GPA)
```

## 免责声明 / Disclaimer

本脚本默认参数均为合理设置，请求频率不高于正常手动操作。若因修改参数（如缩短请求间隔、增加重试次数等）导致流量异常或产生其他后果，由修改者自行承担。

请勿频繁请求，以免给服务器造成压力。请妥善保管个人账号、密码及 Cookie，脚本仅从本地 `.env` 读取凭据，不会上传或泄露。

Default parameters are set to reasonable values, with request frequency not exceeding normal manual operation. Modifying parameters (e.g. reducing intervals, increasing retries) that causes abnormal traffic or other issues is the sole responsibility of the modifier.

Do not send excessive requests. Keep your credentials secure. They are only read from the local `.env` file and are never uploaded or shared.

---

## 🇬🇧 English

Automated login & grade query script for university URP system.

### File Structure

```
IMU-URP/
├── main.py            # Main: login, grade query, terminal output
├── captcha_ocr.py     # Captcha recognition module (ddddocr)
├── encryption.py      # Password encryption reference
├── get_enmethod.py    # Fetch login page to analyze encryption
├── .env               # Student ID & password config
├── .env.example       # Config template
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

### Usage

```bash
cp .env.example .env
# Edit .env with your student ID, password, and URP base URL
pip install -r requirements.txt
python main.py
```

The first run will automatically download the ddddocr model (~10MB).

### Features

| Feature                      | Status      |
|------------------------------|-------------|
| Auto captcha recognition     | ✅          |
| Auto login                   | ✅          |
| All-term grade query         | ✅          |
| Group by semester            | ✅          |
| Weighted average score       | ✅          |
| GPA estimation               | ✅          |
| Exclude pass/fail courses    | ✅          |
| Colored terminal output      | ✅          |
| Manual captcha fallback      | ✅          |
| Course registration          | ⬜ Planned  |

### Sample Output

```
[*] Attempt 1
[*] Fetching login page...
[*] Downloading captcha...
[*] Recognizing captcha...
[*] Result: n5c2
[*] Submitting login...
[OK] Login successful

[2021-2022 Fall]
.------------------------------------------+------+------+------.
| Course                                   | Cr.  | Score| GPA  |
+------------------------------------------+------+------+------+
| Programming Fundamentals A               | 6.0  | 95   | 4.0  |
| Advanced Mathematics                     | 6.0  | 80   | 3.0  |
| English                                  | 3.0  | 93   | 4.0  |
| ...                                      | ...  | ...  | ...  |
'------------------------------------------+------+------+------'

.-------------------------------------.
|  Total Credits: 180  Courses: 60   |
|  Weighted Avg: 85.00  |  GPA: 3.50 |
'-------------------------------------'
[OK] Good (pass/fail courses excluded from GPA)
```


