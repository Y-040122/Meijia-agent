"""
generate_mock_data.py  v3  —— 修复 CVR、曝光下限、波动幅度
字段顺序与 nail_agent_app.py 完全一致：
  日期 / 款式名称 / 曝光数 / 点击数 / 收藏数 / 下单数 / 客单价
"""
import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta

np.random.seed(None)

STYLES = ["猫眼", "法式精修", "纯色", "穿戴甲", "手绘油画"]
N_DAYS = 90
END_DATE   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=N_DAYS - 1)

# 价格区间（按款式类型分层）
PRICE_RANGES = {
    "猫眼":    (180, 280),
    "法式精修": (320, 420),
    "纯色":    (60,  120),
    "穿戴甲":  (90,  150),
    "手绘油画": (380, 480),
}

# 节假日（在数据日期范围内的）
_HOLIDAYS = set()
for _y in [2026]:
    _HOLIDAYS.add(datetime(_y, 3, 8).date())       # 三八
    for _d in range(4, 7):
        _HOLIDAYS.add(datetime(_y, 4, _d).date())  # 清明 4/4-4/6
    for _d in range(1, 6):
        _HOLIDAYS.add(datetime(_y, 5, _d).date())  # 五一 5/1-5/5
    _HOLIDAYS.add(datetime(_y, 6, 1).date())       # 儿童节

# ── 每个款式的隐藏参数（随机生成）──────────────────────────────────────────────
truth        = {}
style_params = {}

for style in STYLES:
    p_lo, p_hi = PRICE_RANGES[style]
    p = {
        "base_exposure": float(np.random.uniform(1500, 6000)),
        "trend_slope":   float(np.random.uniform(-0.04, 0.04)),
        "base_ctr":      float(np.random.uniform(0.10, 0.15)),    # 10-15%
        "base_cvr":      float(np.random.uniform(0.035, 0.065)),  # 3.5-6.5%（关键修复）
        "price_base":    float(np.random.uniform(p_lo, p_hi)),
    }
    style_params[style] = p
    slope = p["trend_slope"]
    truth[style] = {
        "trend_slope":    round(slope, 4),
        "base_exposure":  round(p["base_exposure"], 0),
        "base_ctr":       round(p["base_ctr"], 4),
        "base_cvr":       round(p["base_cvr"], 4),
        "price_base":     round(p["price_base"], 0),
        "interpretation": (
            "明确上升" if slope >  0.02 else
            "缓慢上升" if slope >  0.005 else
            "基本稳定" if slope > -0.005 else
            "缓慢下降" if slope > -0.02 else
            "明确下降"
        ),
    }

# ── 随机异常事件：2 次突涨（×1.6）+ 1 次突跌（×0.7）────────────────────────────
spike_days = np.random.choice(range(N_DAYS), size=2, replace=False)
spike_map  = {int(d): np.random.choice(STYLES) for d in spike_days}
dip_day    = int(np.random.choice(range(N_DAYS)))
dip_style  = np.random.choice(STYLES)
# 确保突跌和突涨不在同一天
while dip_day in spike_map:
    dip_day = int(np.random.choice(range(N_DAYS)))

truth["_random_events"] = {
    "spikes": [
        {"day_index": d,
         "date": (START_DATE + timedelta(days=d)).strftime("%Y-%m-%d"),
         "style": spike_map[d], "effect": "× 1.6 曝光突增"}
        for d in sorted(spike_map)
    ],
    "dips": [
        {"day_index": dip_day,
         "date": (START_DATE + timedelta(days=dip_day)).strftime("%Y-%m-%d"),
         "style": dip_style, "effect": "× 0.7 曝光突降"}
    ],
}

# ── 逐日生成数据 ───────────────────────────────────────────────────────────────
rows  = []
dates = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]

for day_idx, date in enumerate(dates):
    weekend_mult = 1.3 if date.weekday() >= 5 else 1.0
    holiday_mult = 1.5 if date.date() in _HOLIDAYS else 1.0
    base_mult    = max(weekend_mult, holiday_mult)   # 取较大者，不叠加

    for style in STYLES:
        p = style_params[style]

        # 曝光：趋势 × 场景系数 × ±15% 均匀噪声
        trend_factor = max(0.4, 1.0 + p["trend_slope"] * day_idx)
        noise        = 1.0 + np.random.uniform(-0.15, 0.15)
        exposure     = p["base_exposure"] * trend_factor * noise * base_mult

        # 曝光下限：base 的 30%（关键修复：不让曝光跌到地板）
        floor    = p["base_exposure"] * 0.3
        exposure = max(floor, exposure)

        # 叠加随机异常事件
        if day_idx in spike_map and spike_map[day_idx] == style:
            exposure *= 1.6
        if day_idx == dip_day and style == dip_style:
            exposure *= 0.7

        exposure = int(round(exposure))

        # 点击数：CTR = base ± 2%（关键：不超过 base 太多）
        ctr    = max(0.05, min(0.25, p["base_ctr"] + np.random.uniform(-0.02, 0.02)))
        clicks = max(1, int(round(exposure * ctr)))

        # 下单数：曝光 × base_CVR × ±20% 波动（关键修复：直接从曝光算，不从点击算）
        cvr_noise = 1.0 + np.random.uniform(-0.20, 0.20)
        orders    = max(0, int(round(exposure * p["base_cvr"] * cvr_noise)))

        # 收藏数：点击的 25% 左右
        saves = max(0, int(round(clicks * 0.25 * (1 + np.random.uniform(-0.10, 0.10)))))

        # 客单价：base ± 10%
        price = max(30.0, round(p["price_base"] * (1 + np.random.uniform(-0.10, 0.10)), 1))

        rows.append({
            "日期":    date.strftime("%Y-%m-%d"),
            "款式名称": style,
            "曝光数":   exposure,
            "点击数":   clicks,
            "收藏数":   saves,
            "下单数":   orders,
            "客单价":   price,
        })

# ── 写出文件 ───────────────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
df.to_csv("mock_data.csv", index=False, encoding="utf-8-sig")

with open("mock_data_truth.json", "w", encoding="utf-8") as f:
    json.dump(truth, f, ensure_ascii=False, indent=2)

# ── 验证输出 ───────────────────────────────────────────────────────────────────
print("=" * 62)
print(f"mock_data.csv  {len(df)} 行 | {df['日期'].min()} → {df['日期'].max()}")
print(f"最大日曝光 {df['曝光数'].max():,} | 最小日曝光 {df['曝光数'].min():,}")
print()
print(f"{'款式':<10} {'slope':>8}  {'解读':<8}  {'CVR基础':>8}  {'base_exp':>9}  {'价格基础':>8}")
print("  " + "─" * 60)
for style in STYLES:
    t = truth[style]
    print(f"  {style:<10} {t['trend_slope']:>+8.4f}  {t['interpretation']:<8}  "
          f"{t['base_cvr']:>8.2%}  {t['base_exposure']:>9,.0f}  ¥{t['price_base']:>7.0f}")

print()
print("【CVR 实测（应在 2.5-8% 之间）】")
all_ok = True
for style in STYLES:
    sdf = df[df["款式名称"] == style]
    cvr = sdf["下单数"].sum() / sdf["曝光数"].sum() * 100
    ok  = 2.0 <= cvr <= 9.0
    all_ok = all_ok and ok
    print(f"  {'✅' if ok else '⚠️ '} {style}: 实测 CVR = {cvr:.2f}%  |  "
          f"最低日曝光 = {sdf['曝光数'].min():,}")

print()
print("【随机异常事件】")
for ev in truth["_random_events"]["spikes"]:
    print(f"  ↑ 突涨 ×1.6 | {ev['date']}  {ev['style']}")
for ev in truth["_random_events"]["dips"]:
    print(f"  ↓ 突跌 ×0.7 | {ev['date']}  {ev['style']}")

print()
_v = pd.read_csv("mock_data.csv", encoding="utf-8-sig")
assert len(_v) == N_DAYS * len(STYLES), f"行数异常！期望{N_DAYS*len(STYLES)}实际{len(_v)}"
assert list(_v.columns) == ["日期","款式名称","曝光数","点击数","收藏数","下单数","客单价"], "字段名不匹配！"
print(f"pandas 验证通过：{len(_v)} 行，字段 {list(_v.columns)}")
print("=" * 62)
