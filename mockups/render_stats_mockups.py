from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SCALE = 2
W, H = 1280, 900

FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

BLUE = "#2563eb"
GREEN = "#16a34a"
ORANGE = "#f59e0b"
RED = "#ef4444"
VIOLET = "#7c3aed"
CYAN = "#0891b2"
PINK = "#db2777"


def c(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def sc(v):
    return int(round(v * SCALE))


def box(x, y, w, h):
    return (sc(x), sc(y), sc(x + w), sc(y + h))


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, sc(size))


def fmt_hours(value):
    minutes = int(round(value * 60))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h{m}min"
    if h:
        return f"{h}h"
    if m:
        return f"{m}min"
    return "0"


class Mockup:
    def __init__(self):
        self.img = Image.new("RGB", (sc(W), sc(H)), c("#e8edf4"))
        self.d = ImageDraw.Draw(self.img)

    def rr(self, x, y, w, h, fill, outline=None, radius=8, width=1):
        def rounded_fill(x0, y0, x1, y1, r, color):
            r = max(0, min(r, (x1 - x0) // 2, (y1 - y0) // 2))
            self.d.rectangle((x0 + r, y0, x1 - r, y1), fill=color)
            self.d.rectangle((x0, y0 + r, x1, y1 - r), fill=color)
            self.d.pieslice((x0, y0, x0 + 2 * r, y0 + 2 * r), 180, 270, fill=color)
            self.d.pieslice((x1 - 2 * r, y0, x1, y0 + 2 * r), 270, 360, fill=color)
            self.d.pieslice((x1 - 2 * r, y1 - 2 * r, x1, y1), 0, 90, fill=color)
            self.d.pieslice((x0, y1 - 2 * r, x0 + 2 * r, y1), 90, 180, fill=color)

        x0, y0, x1, y1 = box(x, y, w, h)
        r = sc(radius)
        if outline:
            rounded_fill(x0, y0, x1, y1, r, c(outline))
            inset = sc(width)
            rounded_fill(x0 + inset, y0 + inset, x1 - inset, y1 - inset, max(0, r - inset), c(fill))
        else:
            rounded_fill(x0, y0, x1, y1, r, c(fill))

    def rect(self, x, y, w, h, fill, outline=None, width=1):
        self.d.rectangle(
            box(x, y, w, h),
            fill=c(fill),
            outline=c(outline) if outline else None,
            width=sc(width),
        )

    def line(self, x1, y1, x2, y2, fill="#d8dee8", width=1):
        self.d.line((sc(x1), sc(y1), sc(x2), sc(y2)), fill=c(fill), width=sc(width))

    def text(self, x, y, value, size=16, fill="#20242a", bold=False, anchor=None):
        self.d.text((sc(x), sc(y)), value, fill=c(fill), font=font(size, bold), anchor=anchor)

    def center(self, x, y, w, h, value, size=16, fill="#20242a", bold=False):
        f = font(size, bold)
        tw, th = self.d.textsize(value, font=f)
        self.d.text(
            (sc(x) + (sc(w) - tw) / 2, sc(y) + (sc(h) - th) / 2 - sc(1)),
            value,
            fill=c(fill),
            font=f,
        )

    def button(self, x, y, w, h, label, fill="#ffffff", outline="#cbd5e1", fg="#20242a", bold=False):
        self.rr(x, y, w, h, fill, outline, radius=6)
        self.center(x, y, w, h, label, size=15, fill=fg, bold=bold)

    def chip(self, x, y, w, h, label, active=False):
        if active:
            self.rr(x, y, w, h, BLUE, BLUE, radius=6)
            self.center(x, y, w, h, label, size=14, fill="#ffffff", bold=True)
        else:
            self.rr(x, y, w, h, "#f8fafc", "#d6dde8", radius=6)
            self.center(x, y, w, h, label, size=14, fill="#3d4654")

    def window(self, active_tab):
        for i, color in enumerate(["#d9e0ea", "#d2dae5", "#cbd4df"]):
            self.rr(42 + i * 2, 30 + i * 2, 1190, 822, color, None, radius=10)

        self.rr(40, 28, 1190, 820, "#ffffff", "#cfd7e3", radius=10)
        self.rect(40, 28, 1190, 40, "#f6f7f9")
        self.line(40, 68, 1230, 68, "#d9dee7")
        self.text(62, 39, "日记", size=15, bold=True)
        self.text(105, 40, "daily-time-stats", size=13, fill="#6b7280")
        self.button(1104, 37, 30, 20, "-", "#f6f7f9", "#d0d6df")
        self.button(1140, 37, 30, 20, "□", "#f6f7f9", "#d0d6df")
        self.button(1176, 37, 30, 20, "×", "#fff1f1", "#e4b0b0", fg="#9f1d1d", bold=True)

        self.rect(40, 69, 1190, 64, "#ffffff")
        tabs = ["今日时间统计", "一周时间统计", "一月时间统计"]
        tx = 66
        for label in tabs:
            if label == active_tab:
                self.rr(tx, 84, 150, 34, "#eef5ff", "#b7cdf7", radius=6)
                self.center(tx, 84, 150, 34, label, size=15, fill="#1d4ed8", bold=True)
                self.rect(tx + 18, 126, 114, 3, BLUE)
            else:
                self.center(tx, 84, 150, 34, label, size=15, fill="#4b5563")
            tx += 162

        self.button(988, 84, 92, 34, "导出备份")
        self.button(1094, 84, 92, 34, "恢复备份")
        self.rect(40, 133, 1190, 715, "#f7f8fb")

    def range_bar(self, label, value, left_label="<", right_label=">"):
        self.rr(64, 152, 1142, 58, "#ffffff", "#dce3ec", radius=8)
        self.text(88, 171, label, size=14, fill="#667085")
        self.button(152, 162, 34, 34, left_label)
        self.rr(198, 162, 250, 34, "#ffffff", "#cbd5e1", radius=6)
        self.center(198, 162, 250, 34, value, size=15)
        self.button(460, 162, 34, 34, right_label)
        self.button(508, 162, 66, 34, "本期", "#edf7f1", "#b8dfc6", fg="#127040", bold=True)

    def total_card(self, title, value, subtitle=None, subtitle_value=None):
        self.rr(64, 226, 1142, 92, "#ffffff", "#dce3ec", radius=8)
        if subtitle:
            self.center(64, 242, 1142, 26, f"{subtitle}  {subtitle_value}", size=14, fill="#667085")
            self.center(64, 268, 1142, 42, f"{title}  {value}", size=25, fill="#111827", bold=True)
        else:
            self.center(64, 246, 1142, 54, f"{title}  {value}", size=27, fill="#111827", bold=True)

    def chart_card(self, x, y, w, h, title):
        self.rr(x, y, w, h, "#ffffff", "#dce3ec", radius=8)
        self.text(x + 24, y + 20, title, size=18, bold=True)

    def legend(self, x, y, items):
        lx = x
        for label, color in items:
            self.rr(lx, y + 4, 18, 10, color, None, radius=3)
            self.text(lx + 26, y, label, size=12, fill="#4b5563")
            lx += 92

    def axes(self, x, y, w, h, ymax, ticks):
        left, top = x + 58, y + 66
        chart_w, chart_h = w - 90, h - 116
        for t in ticks:
            py = top + chart_h - chart_h * (t / ymax)
            self.line(left, py, left + chart_w, py, "#eef1f5", 1)
            self.text(left - 46, py - 9, fmt_hours(t), size=11, fill="#6b7280")
        self.line(left, top, left, top + chart_h, "#cbd5e1", 1)
        self.line(left, top + chart_h, left + chart_w, top + chart_h, "#cbd5e1", 1)
        return left, top, chart_w, chart_h

    def bars(self, x, y, w, h, title, labels, values, ymax, ticks, color=BLUE):
        self.chart_card(x, y, w, h, title)
        left, top, chart_w, chart_h = self.axes(x, y, w, h, ymax, ticks)
        slot = chart_w / len(labels)
        bar_w = min(30, slot * 0.48)
        base = top + chart_h
        for i, (label, value) in enumerate(zip(labels, values)):
            cx = left + slot * i + slot / 2
            bh = chart_h * (value / ymax)
            self.rr(cx - bar_w / 2, base - bh, bar_w, bh, color, None, radius=4)
            self.center(cx - slot / 2, base + 13, slot, 24, label, size=12, fill="#4b5563")

    def grouped_bars(self, x, y, w, h, title, labels, series, ymax, ticks, legend_items):
        self.chart_card(x, y, w, h, title)
        self.legend(x + 240, y + 23, legend_items)
        left, top, chart_w, chart_h = self.axes(x, y, w, h, ymax, ticks)
        slot = chart_w / len(labels)
        group_count = len(series)
        bar_w = min(16, slot * 0.72 / group_count)
        base = top + chart_h
        for i, label in enumerate(labels):
            cx = left + slot * i + slot / 2
            start = cx - (bar_w * group_count + 3 * (group_count - 1)) / 2
            for j, (_, values, color) in enumerate(series):
                value = values[i]
                bh = chart_h * (value / ymax)
                bx = start + j * (bar_w + 3)
                self.rr(bx, base - bh, bar_w, bh, color, None, radius=3)
            self.center(cx - slot / 2, base + 13, slot, 24, label, size=12, fill="#4b5563")

    def lines_chart(self, x, y, w, h, title, labels, series, ymax, ticks, legend_items=None):
        self.chart_card(x, y, w, h, title)
        if legend_items:
            self.legend(x + 245, y + 23, legend_items)
        left, top, chart_w, chart_h = self.axes(x, y, w, h, ymax, ticks)
        step = chart_w / (len(labels) - 1)
        base = top + chart_h
        for i, label in enumerate(labels):
            px = left + step * i
            self.center(px - 24, base + 13, 48, 24, label, size=12, fill="#4b5563")
        for _, values, color in series:
            points = []
            for i, value in enumerate(values):
                px = left + step * i
                py = base - chart_h * (value / ymax)
                points.append((sc(px), sc(py)))
            self.d.line(points, fill=c(color), width=sc(3))
            for px, py in points:
                self.d.ellipse((px - sc(4), py - sc(4), px + sc(4), py + sc(4)), fill=c("#ffffff"), outline=c(color), width=sc(2))

    def save(self, name):
        out = ROOT / name
        self.img.resize((W, H), Image.LANCZOS).save(out)
        print(out)


CATS = ["调研", "学习", "阅读", "代码", "写作", "沟通", "休息"]
DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WEEK_COLORS = [BLUE, GREEN, ORANGE, VIOLET]


def render_week_default():
    m = Mockup()
    m.window("一周时间统计")
    m.range_bar("周范围", "2026-06-01 至 2026-06-07")
    m.total_card("本周总时长", "42小时35分钟")
    m.bars(64, 338, 552, 378, "事项用时", CATS, [4.5, 7.0, 3.0, 10.5, 6.0, 5.0, 6.5], 12, [0, 3, 6, 9, 12])
    m.lines_chart(
        654,
        338,
        552,
        378,
        "每日用时",
        DAYS,
        [("本周", [6, 7, 5.5, 8, 7.5, 4, 4.5], BLUE)],
        8,
        [0, 2, 4, 6, 8],
    )
    m.button(542, 764, 196, 38, "与上周对比", "#111827", "#111827", fg="#ffffff", bold=True)
    m.save("week-page.png")


def render_week_compare():
    m = Mockup()
    m.window("一周时间统计")
    m.range_bar("周范围", "2026-06-01 至 2026-06-07")
    m.total_card("本周总时长", "42小时35分钟", "上周总时长", "39小时10分钟")
    m.grouped_bars(
        64,
        338,
        552,
        378,
        "事项用时",
        CATS,
        [
            ("上周", [4.0, 6.5, 2.5, 9.0, 5.0, 5.5, 6.5], "#94a3b8"),
            ("本周", [4.5, 7.0, 3.0, 10.5, 6.0, 5.0, 6.5], BLUE),
        ],
        12,
        [0, 3, 6, 9, 12],
        [("上周", "#94a3b8"), ("本周", BLUE)],
    )
    m.lines_chart(
        654,
        338,
        552,
        378,
        "每日用时",
        DAYS,
        [
            ("上周", [5, 6.5, 6, 6.5, 6, 4.5, 4], "#94a3b8"),
            ("本周", [6, 7, 5.5, 8, 7.5, 4, 4.5], BLUE),
        ],
        8,
        [0, 2, 4, 6, 8],
        [("上周", "#94a3b8"), ("本周", BLUE)],
    )
    m.button(542, 764, 196, 38, "关闭对比", "#ffffff", "#cbd5e1", fg="#20242a", bold=True)
    m.save("week-compare-page.png")


def render_month_day():
    m = Mockup()
    m.window("一月时间统计")
    m.range_bar("月份", "2026-06")
    m.chip(988, 162, 92, 34, "按日统计", active=True)
    m.chip(1094, 162, 92, 34, "按周统计", active=False)
    m.total_card("本月总时长", "198小时20分钟")
    m.bars(64, 338, 552, 378, "事项用时", CATS, [22.5, 31, 18, 45, 26.5, 21, 34.5], 48, [0, 12, 24, 36, 48])
    m.lines_chart(
        654,
        338,
        552,
        378,
        "每日用时",
        DAYS,
        [("按星期聚合", [27, 30.5, 28, 33, 31.5, 23, 25.5], BLUE)],
        36,
        [0, 9, 18, 27, 36],
    )
    m.text(88, 778, "当前模式：按星期聚合显示本月各星期用时", size=13, fill="#667085")
    m.save("month-day-page.png")


def render_month_week():
    m = Mockup()
    m.window("一月时间统计")
    m.range_bar("月份", "2026-06")
    m.chip(988, 162, 92, 34, "按日统计", active=False)
    m.chip(1094, 162, 92, 34, "按周统计", active=True)
    m.total_card("本月总时长", "198小时20分钟")
    series = [
        ("第一周", [5, 7, 4, 10, 6, 4.5, 6], BLUE),
        ("第二周", [6, 8, 5, 11, 7, 5.5, 7], GREEN),
        ("第三周", [5.5, 7.5, 4.5, 12, 6.5, 5, 8], ORANGE),
        ("第四周", [6, 8.5, 4, 12, 7, 6, 7.5], VIOLET),
    ]
    legend = [(name, color) for name, _, color in series]
    m.grouped_bars(64, 338, 552, 378, "事项用时", CATS, series, 12, [0, 3, 6, 9, 12], legend)
    m.lines_chart(
        654,
        338,
        552,
        378,
        "每日用时",
        DAYS,
        [
            ("第一周", [6, 7, 5, 8, 7, 4, 5], BLUE),
            ("第二周", [7, 7.5, 6, 8.5, 8, 5, 5.5], GREEN),
            ("第三周", [6.5, 8, 6, 9, 7.5, 5.5, 6], ORANGE),
            ("第四周", [7, 8.5, 6.5, 9.5, 8, 5.5, 6.5], VIOLET),
        ],
        10,
        [0, 2.5, 5, 7.5, 10],
        legend,
    )
    m.text(88, 778, "纳入统计周：周一、周日均在本月内的完整周", size=13, fill="#667085")
    m.save("month-week-page.png")


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    render_week_default()
    render_week_compare()
    render_month_day()
    render_month_week()
