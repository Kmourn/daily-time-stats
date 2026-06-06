# 日记 / daily-time-stats

Ubuntu 桌面版每日时间统计程序。

## 功能

- 今日时间统计：手动录入、开始/结束计时、多段时间、编辑删除。
- 一周时间统计：本周总时长、事项柱状图、每日折线图、与上周对比。
- 一月时间统计：按日统计、按周统计。
- 本地 SQLite 数据库存储。
- 手动导出/恢复备份，今日事项完毕时自动备份，自动备份保留最近 7 份。
- 托盘常驻、从托盘恢复、结束当前计时、退出。

## 开发运行

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m daily_time_stats
```

## 构建 .deb

```bash
scripts/build_deb.sh
```

构建产物会输出到 `dist/deb/`。
