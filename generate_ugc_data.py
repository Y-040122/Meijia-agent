"""
generate_ugc_data.py
生成 UGC 中心所需的两个数据文件：
  ugc_external.csv  —— 外部平台信号（90天×10款式×3平台，2700行）
  ugc_internal.json —— 本店内部 UGC 资产（定量随机 + 定性预设池抽取）
"""
import numpy as np
import pandas as pd
import json
import random
from datetime import datetime, timedelta

np.random.seed(None)
random.seed(None)

N_DAYS = 90
END_DATE   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=N_DAYS - 1)
dates = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]

# ══════════════════════════════════════════════════════════════════════════════
# Part 1 ── ugc_external.csv
# ══════════════════════════════════════════════════════════════════════════════
EXT_STYLES = [
    "猫眼", "纯欲风", "法式", "穿戴甲", "手绘油画风",
    "冰透果冻甲", "流沙猫眼", "古风晕染", "磨砂质感", "彩绘新潮",
]
PLATFORMS = ["社交平台A", "社交平台B", "社交平台C"]
# 情感分布：80% 正面 / 15% 中性 / 5% 负面
SENTIMENT_POOL = ["正面"] * 80 + ["中性"] * 15 + ["负面"] * 5

ext_params = {
    s: {
        "base_notes":       float(np.random.uniform(200, 3000)),
        "trend_slope":      float(np.random.uniform(-0.05, 0.05)),
        "interaction_coef": float(np.random.uniform(8, 15)),
    }
    for s in EXT_STYLES
}

rows_ext = []
for day_idx, date in enumerate(dates):
    for style in EXT_STYLES:
        p = ext_params[style]
        trend = max(0.2, 1.0 + p["trend_slope"] * day_idx)
        for platform in PLATFORMS:
            platform_mult = {"社交平台A": 1.0, "社交平台B": 0.60, "社交平台C": 0.40}[platform]
            noise  = 1.0 + np.random.uniform(-0.25, 0.25)
            notes  = max(1, int(round(p["base_notes"] * trend * noise * platform_mult)))
            inter  = max(1, int(round(notes * p["interaction_coef"] * (1 + np.random.uniform(-0.10, 0.10)))))
            senti  = random.choice(SENTIMENT_POOL)
            rows_ext.append({
                "日期":    date.strftime("%Y-%m-%d"),
                "款式名":   style,
                "平台来源": platform,
                "笔记数":   notes,
                "互动量":   inter,
                "情感倾向": senti,
            })

df_ext = pd.DataFrame(rows_ext)
df_ext.to_csv("ugc_external.csv", index=False, encoding="utf-8-sig")

# ══════════════════════════════════════════════════════════════════════════════
# Part 2 ── ugc_internal.json
# ══════════════════════════════════════════════════════════════════════════════
# ── 预设池（写死在脚本里，内容固定，数量随机）─────────────────────────────────────

POS_TAGS_POOL = [
    "果冻甲专门店", "猫眼工艺标杆", "法式精修达人", "纯欲风出片好",
    "手绘个性款拿手", "美甲师手艺细腻", "服务好评率高", "店内环境干净",
    "性价比不错", "拆甲不伤指甲", "持久度长", "提前预约方便",
    "美甲师沟通耐心", "可以加V微改图", "推新款积极",
]
NEG_TAGS_POOL = [
    "排队等位久", "周末预约难", "拆甲收费偏贵", "复购优惠少",
    "停车不方便", "店内空间小", "高峰期等位长", "预约改期手续繁琐",
]
COMPLAINT_POOL = [
    {"话题": "猫眼款颜色不够透",    "样本": "图片里很亮，做出来颜色暗了很多",    "关联款式": "猫眼"},
    {"话题": "法式甲线条不够直",    "样本": "右手大拇指那条线明显歪了",          "关联款式": "法式精修"},
    {"话题": "手绘款实际效果差异大", "样本": "图片精致但做出来粗糙了不少",        "关联款式": "手绘油画"},
    {"话题": "穿戴甲不够贴合",      "样本": "戴几天就翘起来了",                  "关联款式": "穿戴甲"},
    {"话题": "纯色不够饱满",        "样本": "颜色刷得有点稀薄",                  "关联款式": "纯色"},
    {"话题": "周末排队时间过长",     "样本": "周六下午等了快一个半小时",          "关联款式": "全店"},
    {"话题": "拆甲收费偏贵",        "样本": "拆甲单独收30块感觉有点贵",          "关联款式": "全店"},
    {"话题": "复购优惠力度小",      "样本": "老客户没有专属折扣",                 "关联款式": "全店"},
]
STYLE_UGC_POOL = {
    "猫眼":    {"好评候选": ["工艺细腻", "色彩饱满"],    "差评候选": ["颜色透感不足", "细节处理粗糙"]},
    "法式精修": {"好评候选": ["线条干净", "修甲精细"],    "差评候选": ["无", "线条不够直"]},
    "纯色":    {"好评候选": ["服务到位", "上色均匀"],    "差评候选": ["无", "颜色不够饱满"]},
    "穿戴甲":  {"好评候选": ["性价比高", "佩戴简单"],    "差评候选": ["持久度一般", "不够贴合"]},
    "手绘油画": {"好评候选": ["独特性强", "创意性高"],    "差评候选": ["等待时间长", "效果差异大"]},
}

# ── 心智标签（4正+1负，共5个）────────────────────────────────────────────────
sel_pos = random.sample(POS_TAGS_POOL, 4)
sel_neg = random.sample(NEG_TAGS_POOL, 1)
all_tags = [(t, "正面") for t in sel_pos] + [(t, "负面") for t in sel_neg]
random.shuffle(all_tags)
freqs      = [random.randint(20, 100) for _ in all_tags]
total_freq = sum(freqs)
心智标签 = [
    {"标签": tag, "类型": typ, "频次": freq, "权重": round(freq / total_freq, 3)}
    for (tag, typ), freq in zip(all_tags, freqs)
]

# ── 差评话题（随机抽3个不重复）────────────────────────────────────────────────
sel_complaints = random.sample(COMPLAINT_POOL, 3)
差评话题 = [
    {
        "话题":     c["话题"],
        "样本":     c["样本"],
        "关联款式": c["关联款式"],
        "提及次数": random.randint(3, 15),
        "占差评比": round(random.uniform(0.15, 0.65), 2),
    }
    for c in sel_complaints
]

# ── 款式UGC表现（5个款式）────────────────────────────────────────────────────
款式UGC = {}
INT_STYLES = ["猫眼", "法式精修", "纯色", "穿戴甲", "手绘油画"]
for style in INT_STYLES:
    pool = STYLE_UGC_POOL[style]
    款式UGC[style] = {
        "本店UGC数": random.randint(20, 100),
        "好评率":    round(random.uniform(0.78, 0.97), 2),
        "核心好评":  random.choice(pool["好评候选"]),
        "核心差评":  random.choice(pool["差评候选"]),
    }

# ── 汇总数字（全部随机）────────────────────────────────────────────────────────
ugc_internal = {
    "总条数":      random.randint(200, 400),
    "本月新增":    random.randint(30, 70),
    "好评率":      round(random.uniform(0.85, 0.96), 2),
    "晒图率":      round(random.uniform(0.25, 0.45), 2),
    "UGC引流订单": random.randint(8, 20),
    "心智标签":   心智标签,
    "差评话题":   差评话题,
    "款式UGC":    款式UGC,
}

with open("ugc_internal.json", "w", encoding="utf-8") as f:
    json.dump(ugc_internal, f, ensure_ascii=False, indent=2)

# ── 验证输出 ───────────────────────────────────────────────────────────────────
print("=" * 62)
print(f"ugc_external.csv: {len(df_ext)} 行 "
      f"（{len(EXT_STYLES)} 款式 × {N_DAYS} 天 × {len(PLATFORMS)} 平台）")
print(f"ugc_internal.json: 已生成")
print()
print(f"总条数={ugc_internal['总条数']}  本月新增={ugc_internal['本月新增']}")
print(f"好评率={ugc_internal['好评率']:.0%}  晒图率={ugc_internal['晒图率']:.0%}  "
      f"UGC引流订单={ugc_internal['UGC引流订单']} 单")
print()
print("抽中的 5 个心智标签：")
for t in 心智标签:
    print(f"  [{'正' if t['类型']=='正面' else '负'}] {t['标签']}  频次={t['频次']}  权重={t['权重']:.1%}")
print()
print("抽中的 3 个差评话题：")
for c in 差评话题:
    print(f"  [{c['关联款式']}] {c['话题']}  提及={c['提及次数']}  占比={c['占差评比']:.0%}")
print()
print("款式 UGC 表现：")
for sty in INT_STYLES:
    u = 款式UGC[sty]
    print(f"  {sty}: UGC数={u['本店UGC数']}  好评率={u['好评率']:.0%}"
          f"  好评='{u['核心好评']}'  差评='{u['核心差评']}'")
print("=" * 62)
