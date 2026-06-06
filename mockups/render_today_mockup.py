from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "today-page.png"

SCALE = 2
W, H = 1280, 900

FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def c(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def sc(v):
    return int(round(v * SCALE))


def box(x, y, w, h):
    return (sc(x), sc(y), sc(x + w), sc(y + h))


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, sc(size))


img = Image.new("RGB", (sc(W), sc(H)), c("#e8edf4"))
d = ImageDraw.Draw(img)


def rr(x, y, w, h, fill, outline=None, radius=8, width=1):
    def rounded_fill(x0, y0, x1, y1, r, color):
        r = max(0, min(r, (x1 - x0) // 2, (y1 - y0) // 2))
        d.rectangle((x0 + r, y0, x1 - r, y1), fill=color)
        d.rectangle((x0, y0 + r, x1, y1 - r), fill=color)
        d.pieslice((x0, y0, x0 + 2 * r, y0 + 2 * r), 180, 270, fill=color)
        d.pieslice((x1 - 2 * r, y0, x1, y0 + 2 * r), 270, 360, fill=color)
        d.pieslice((x1 - 2 * r, y1 - 2 * r, x1, y1), 0, 90, fill=color)
        d.pieslice((x0, y1 - 2 * r, x0 + 2 * r, y1), 90, 180, fill=color)

    x0, y0, x1, y1 = box(x, y, w, h)
    r = sc(radius)
    if outline:
        rounded_fill(x0, y0, x1, y1, r, c(outline))
        inset = sc(width)
        rounded_fill(x0 + inset, y0 + inset, x1 - inset, y1 - inset, max(0, r - inset), c(fill))
    else:
        rounded_fill(x0, y0, x1, y1, r, c(fill))


def rect(x, y, w, h, fill, outline=None, width=1):
    d.rectangle(
        box(x, y, w, h),
        fill=c(fill),
        outline=c(outline) if outline else None,
        width=sc(width),
    )


def line(x1, y1, x2, y2, fill="#d8dee8", width=1):
    d.line((sc(x1), sc(y1), sc(x2), sc(y2)), fill=c(fill), width=sc(width))


def text(x, y, value, size=16, fill="#20242a", bold=False, anchor=None):
    d.text((sc(x), sc(y)), value, fill=c(fill), font=font(size, bold), anchor=anchor)


def text_center(x, y, w, h, value, size=16, fill="#20242a", bold=False):
    f = font(size, bold)
    tw, th = d.textsize(value, font=f)
    d.text(
        (sc(x) + (sc(w) - tw) / 2, sc(y) + (sc(h) - th) / 2 - sc(1)),
        value,
        fill=c(fill),
        font=f,
    )


def button(x, y, w, h, label, fill="#ffffff", outline="#cbd5e1", fg="#20242a", bold=False):
    rr(x, y, w, h, fill, outline, radius=6)
    text_center(x, y, w, h, label, size=15, fill=fg, bold=bold)


def pill(x, y, w, h, label, active=False):
    if active:
        rr(x, y, w, h, "#2563eb", "#2563eb", radius=6)
        text_center(x, y, w, h, label, size=14, fill="#ffffff", bold=True)
    else:
        rr(x, y, w, h, "#f8fafc", "#d6dde8", radius=6)
        text_center(x, y, w, h, label, size=14, fill="#3d4654")


def field(x, y, w, h, label, value, arrow=False):
    text(x, y - 24, label, size=14, fill="#667085")
    rr(x, y, w, h, "#ffffff", "#cbd5e1", radius=6)
    text(x + 12, y + 10, value, size=15, fill="#20242a")
    if arrow:
        text(x + w - 24, y + 10, "v", size=15, fill="#667085", bold=True)


# Window shadow and frame
for i, alpha_color in enumerate(["#d9e0ea", "#d2dae5", "#cbd4df"]):
    rr(42 + i * 2, 30 + i * 2, 1190, 822, alpha_color, None, radius=10)

rr(40, 28, 1190, 820, "#ffffff", "#cfd7e3", radius=10)

# Native-like title bar
rect(40, 28, 1190, 40, "#f6f7f9")
line(40, 68, 1230, 68, "#d9dee7")
text(62, 39, "日记", size=15, bold=True)
text(105, 40, "daily-time-stats", size=13, fill="#6b7280")
button(1104, 37, 30, 20, "-", "#f6f7f9", "#d0d6df")
button(1140, 37, 30, 20, "□", "#f6f7f9", "#d0d6df")
button(1176, 37, 30, 20, "×", "#fff1f1", "#e4b0b0", fg="#9f1d1d", bold=True)

# Top tabs and actions
rect(40, 69, 1190, 64, "#ffffff")
tabs = [("今日时间统计", True), ("一周时间统计", False), ("一月时间统计", False)]
tx = 66
for label, active in tabs:
    if active:
        rr(tx, 84, 150, 34, "#eef5ff", "#b7cdf7", radius=6)
        text_center(tx, 84, 150, 34, label, size=15, fill="#1d4ed8", bold=True)
        rect(tx + 18, 126, 114, 3, "#2563eb")
    else:
        text_center(tx, 84, 150, 34, label, size=15, fill="#4b5563")
    tx += 162

button(988, 84, 92, 34, "导出备份")
button(1094, 84, 92, 34, "恢复备份")

# Page body
rect(40, 133, 1190, 715, "#f7f8fb")

# Date selector band
rr(64, 152, 1142, 58, "#ffffff", "#dce3ec", radius=8)
text(88, 171, "日期", size=14, fill="#667085")
button(135, 162, 34, 34, "<")
rr(180, 162, 150, 34, "#ffffff", "#cbd5e1", radius=6)
text_center(180, 162, 150, 34, "2026-06-06", size=15)
button(340, 162, 34, 34, ">")
button(388, 162, 58, 34, "今天", "#edf7f1", "#b8dfc6", fg="#127040", bold=True)
text(1010, 171, "当日总计", size=13, fill="#667085")
text(1078, 167, "8小时17分钟", size=18, fill="#111827", bold=True)

# Entry form
rr(64, 226, 760, 286, "#ffffff", "#dce3ec", radius=8)
text(88, 248, "新增 / 编辑条目", size=18, bold=True)
text(88, 286, "事项", size=14, fill="#667085")
cats = ["调研", "学习", "阅读", "代码", "写作", "沟通", "休息"]
cx = 88
for cat in cats:
    pill(cx, 310, 72, 34, cat, active=(cat == "代码"))
    cx += 78

field(88, 376, 260, 38, "内容", "PySide6 主窗口", arrow=True)
field(372, 376, 226, 38, "备注", "Ubuntu 20.04 适配")
button(622, 376, 124, 38, "+ 新增时间段", "#eef6ff", "#bdd2f4", fg="#1d4ed8", bold=True)

text(88, 453, "时间段", size=14, fill="#667085")
rr(146, 441, 294, 34, "#f8fafc", "#d8dee8", radius=6)
text(158, 449, "第1段  13:30:00 - 15:12:44", size=14)
button(452, 441, 52, 34, "删除")
rr(522, 441, 294, 34, "#f8fafc", "#d8dee8", radius=6)
text(534, 449, "第2段  16:10:05 - 17:03:18", size=14)

button(620, 248, 94, 36, "保存条目", "#2563eb", "#2563eb", fg="#ffffff", bold=True)
button(724, 248, 72, 36, "清空")

# Timer panel
rr(842, 226, 364, 286, "#ffffff", "#dce3ec", radius=8)
text(866, 248, "计时器", size=18, bold=True)
text(866, 286, "当前选择", size=14, fill="#667085")
rr(866, 310, 278, 38, "#f8fafc", "#d8dee8", radius=6)
text(882, 319, "代码 / PySide6 主窗口", size=15)
text_center(866, 366, 278, 60, "00:00:00", size=36, bold=True)
button(866, 444, 118, 40, "开始", "#16a34a", "#16a34a", fg="#ffffff", bold=True)
button(998, 444, 118, 40, "结束", "#f3f4f6", "#d1d5db", fg="#9ca3af", bold=True)
text(866, 492, "状态：当前未计时", size=13, fill="#667085")

# Entries list
rr(64, 532, 1142, 248, "#ffffff", "#dce3ec", radius=8)
text(88, 555, "2026-06-06 条目", size=18, bold=True)
text(1080, 559, "共 4 条", size=13, fill="#667085")

header_y = 590
rect(88, header_y, 1078, 34, "#f1f4f8")
headers = [("事项", 106), ("内容", 260), ("时间段", 430), ("时长", 116), ("备注", 158), ("操作", 108)]
hx = 88
for label, width in headers:
    text(hx + 12, header_y + 8, label, size=13, fill="#4b5563", bold=True)
    hx += width

rows = [
    ("调研", "#e0f2fe", "#075985", "Ubuntu 20.04 托盘行为", "第1段 09:15:20-10:42:58\n第2段 11:05:12-11:38:40", "2小时1分钟", "方案确认", True),
    ("代码", "#dcfce7", "#166534", "PySide6 主窗口", "第1段 13:30:00-15:12:44\n第2段 16:10:05-17:03:18", "2小时36分钟", "进行中", True),
    ("阅读", "#fef3c7", "#92400e", "QtCharts 文档", "第1段 19:20:12-20:04:55", "0小时45分钟", "", False),
]

ry = 624
for idx, row in enumerate(rows):
    bg = "#ffffff" if idx % 2 == 0 else "#fbfcfe"
    rect(88, ry, 1078, 54, bg)
    rr(102, ry + 13, 52, 26, row[1], None, radius=6)
    text_center(102, ry + 13, 52, 26, row[0], size=13, fill=row[2], bold=True)
    text(194, ry + 12, row[3], size=14)
    tlines = row[4].split("\n")
    text(454, ry + 7, tlines[0], size=13)
    if len(tlines) > 1:
        text(454, ry + 29, tlines[1], size=13, fill="#4b5563")
    text(884, ry + 16, row[5], size=14, bold=True)
    text(1000, ry + 16, row[6] if row[6] else "-", size=13, fill="#4b5563")
    button(1098, ry + 12, 44, 28, "编辑")
    button(1148, ry + 12, 44, 28, "删除", fg="#b42318")
    line(88, ry + 54, 1166, ry + 54, "#edf0f5")
    ry += 54

# Bottom completion area
line(64, 798, 1206, 798, "#dce3ec")
button(542, 810, 196, 38, "今日事项完毕", "#111827", "#111827", fg="#ffffff", bold=True)
text(760, 821, "本日数据未备份", size=13, fill="#9a3412")
text(88, 821, "自动备份保留最近 7 份", size=12, fill="#6b7280")

img = img.resize((W, H), Image.LANCZOS)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(OUT)
