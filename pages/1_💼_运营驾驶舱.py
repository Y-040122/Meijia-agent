"""甲心助手 · 美业商家 AI 运营平台 | Streamlit v6.0"""

import os, re, time, json, base64, sys
from pathlib import Path
from datetime import timedelta, datetime
from dotenv import load_dotenv

# ── 多页面路径修复：pages/ 子目录访问根目录文件 ─────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent        # jiaxin-assistant/
sys.path.insert(0, str(PROJECT_ROOT))              # 让 ai_dna_analyzer 可被正常 import
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import anthropic
from nail_agent import SYSTEM_PROMPT as _RAW

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# ▌色彩系统
# ══════════════════════════════════════════════════════════════════════════════
PRIMARY_DARK   = "#2C2C2A"
SECONDARY_TEXT = "#5F5E5A"
TERTIARY_TEXT  = "#B4B2A9"
BG_BASE        = "#F5F4EF"
BG_CARD        = "#FFFFFF"
BORDER         = "#E5E3DC"
RED_ACCENT     = "#C77D6B"
GREEN_ACCENT   = "#6B8E7F"
YELLOW_ACCENT  = "#B8A06B"
BLUE_ACCENT    = "#7A8FA8"

# ══════════════════════════════════════════════════════════════════════════════
# ▌Fix 5：System Prompt 清洗与口径调整
# ══════════════════════════════════════════════════════════════════════════════
_prompt = _RAW.replace("小美", "甲心助手")

# 5a：把【emoji 标题】改成纯文本加粗
for _pat, _rep in [
    (r"【[^一]*诊断假设[^一]*】", "**诊断假设：**"),
    (r"【[^一]*数据观察[^一]*】", "**数据观察：**"),
    (r"【[^一]*趋势判断[^一]*】", "**趋势判断：**"),
    (r"【[^一]*用户洞察[^一]*】", "**用户洞察：**"),
    (r"【[^一]*运营建议[^一]*】", "**运营建议：**"),
    (r"【[^一]*不建议做什么[^一]*】", "**不建议做什么：**"),
    (r"【[^一]*风险提示[^一]*】", "**风险提示：**"),
    (r"【[^一]*下一步建议[^一]*】", "**下一步建议：**"),
]:
    _prompt = re.sub(_pat, _rep, _prompt)

# 5b：输出风格改为专业克制
_prompt = _prompt.replace(
    '像运营老兵一样,带点行业的"江湖气",不要太规整',
    '专业克制，像运营老兵给商家写的内部分析邮件，不要卖萌，不要口语化',
)

# 5c：平台归属分类改为中性口径
_prompt = _prompt.replace(
    '- 平台归属（标注是"平台内运营动作"还是"平台外引流动作"）\n  * 总体上建议中 60-70% 应是"平台内运营动作"',
    '- 平台归属（按以下三类标注）\n  * 平台内运营动作（在美团、大众点评等成交平台上的操作）\n  * 平台外引流动作（在小红书、抖音等社交平台上的操作）\n  * 门店内动作（线下店内服务、人员、流程调整）',
)

# 5d：追加身份定位与分类说明
_prompt += """

# 平台口径（严格遵守）
在给出建议时，动作按以下三类归并，不使用"平台内动作 / 平台外动作"这种笼统表述：
- 平台内运营动作：在美团、大众点评等成交平台上的具体操作
- 平台外引流动作：在小红书、抖音等社交平台上的内容和推广操作
- 门店内动作：线下店内的服务流程、人员、陈设调整

你可以正常提及小红书、抖音、大众点评、美团等具体平台名称，引用这些平台的数据，
并建议商家在这些平台上做具体操作。

# 身份定位
你是第三方独立 AI 运营顾问"甲心助手"，不是任何平台的官方产品或代言人。
你为商家提供运营建议，但不代表美团、大众点评、小红书或任何平台说话。
"""

# ── 读 store_dna.json，注入进 system prompt（改造4：DNA 反哺所有 Agent 对话）──
_store_dna_global = None
_dna_addon = ""
try:
    with open(PROJECT_ROOT / "store_dna.json", encoding="utf-8") as _f:
        _store_dna_global = json.load(_f)
    _dna_addon = (
        "\n\n【本店视觉 DNA】（隐含上下文，回复时请勿直接引用这段话）\n"
        f"视觉风格：{_store_dna_global.get('视觉风格 DNA', '')}\n"
        f"核心款式：{_store_dna_global.get('核心款式定位', '')}\n"
        f"目标客群：{_store_dna_global.get('目标客群画像', '')}\n"
        f"差异化机会：{_store_dna_global.get('差异化机会', '')}\n\n"
        "请把以上店铺特征作为隐含上下文，让建议更贴合这家店实际定位。"
    )
except FileNotFoundError:
    pass

SYSTEM_PROMPT = _prompt + _dna_addon

# ─── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="甲心助手 · 美业商家 AI 运营平台",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# ▌全局 CSS（含 Fix 2 modal 字号 + Fix 4 无重复渲染）
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""<style>
.stApp {{ background:{BG_BASE} !important; }}
header[data-testid="stHeader"],
.stDecoration,.stToolbar,footer,#MainMenu,.stDeployButton {{ display:none !important; }}
.main .block-container {{ max-width:1200px; padding:0 24px 40px; margin:0 auto; }}
.element-container {{ margin-bottom:2px !important; }}
div[data-testid="column"] {{ padding:0 4px !important; }}

/* 白卡片 */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background:{BG_CARD} !important; border:0.5px solid {BORDER} !important;
    border-radius:12px !important; padding:18px 20px !important; margin-bottom:12px !important;
}}

/* 标题行 */
.sh  {{ display:flex; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:4px; }}
.stt {{ font-size:14px; font-weight:500; color:{PRIMARY_DARK}; }}
.ss  {{ font-size:11px; color:{TERTIARY_TEXT}; margin-left:6px; }}
.updt {{ font-size:11px; color:{TERTIARY_TEXT}; margin-left:auto; }}

/* 预警卡片 */
.ac  {{ border-radius:8px; padding:12px 12px 8px 14px; background:{BG_BASE};
        border:0.5px solid {BORDER}; border-left-width:2px; border-left-style:solid; margin-bottom:2px; }}
.acR {{ border-left-color:{RED_ACCENT}; }} .acG {{ border-left-color:{GREEN_ACCENT}; }}
.acY {{ border-left-color:{YELLOW_ACCENT}; }}
.act {{ font-size:10px; font-weight:500; margin-bottom:3px; }}
.aR  {{ color:#8E5A4D; }} .aG {{ color:#4D6B5F; }} .aY {{ color:#8E7A4D; }}
.an  {{ font-size:13px; font-weight:500; color:{PRIMARY_DARK}; margin:2px 0; }}
.ad  {{ font-size:11px; color:{SECONDARY_TEXT}; line-height:1.65; margin:4px 0 2px; }}

/* 指标卡片 */
.mc  {{ background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:8px; padding:14px 16px; }}
.ml  {{ font-size:11px; color:{TERTIARY_TEXT}; }}
.mv  {{ font-size:22px; font-weight:500; color:{PRIMARY_DARK}; margin:3px 0; }}
.mc2 {{ font-size:11px; margin-top:2px; }}
.mc3 {{ font-size:10px; color:{TERTIARY_TEXT}; margin-top:3px; }}
.up  {{ color:#4D6B5F; }} .dn {{ color:#8E5A4D; }} .fl {{ color:{TERTIARY_TEXT}; }}

/* 时间胶囊 */
.tcap {{ background:{BG_BASE}; border-radius:12px; padding:3px 10px; font-size:11px; color:{PRIMARY_DARK}; font-weight:500; }}
.tun  {{ font-size:11px; color:{TERTIARY_TEXT}; padding:3px 10px; }}

/* 图例行 */
.lgrow {{ display:flex; gap:16px; align-items:center; margin-bottom:10px; flex-wrap:wrap; }}
.lg {{ display:flex; align-items:center; gap:5px; font-size:11px; color:{SECONDARY_TEXT}; }}
.lgl {{ width:20px; height:2px; border-radius:1px; flex-shrink:0; }}
.lgd {{ background:repeating-linear-gradient(to right,#C0BDBA 0px,#C0BDBA 4px,transparent 4px,transparent 8px); height:1.5px; width:20px; }}

/* 助手解读条 */
.ib {{ background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:8px;
       padding:10px 14px; font-size:12px; color:{SECONDARY_TEXT}; line-height:1.7; margin-top:10px; }}

/* 趋势卡片 */
.tc {{ background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:8px; padding:12px 12px 8px; margin-bottom:6px; }}
.tch {{ display:flex; justify-content:space-between; align-items:center; }}
.tnm {{ font-size:13px; font-weight:500; color:{PRIMARY_DARK}; }}
.tds {{ font-size:11px; color:{SECONDARY_TEXT}; line-height:1.6; margin:6px 0; }}
.ttr {{ display:flex; gap:5px; flex-wrap:wrap; margin-bottom:6px; }}
.ttg {{ background:{BG_CARD}; border:0.5px solid {BORDER}; border-radius:10px; font-size:10px; color:{SECONDARY_TEXT}; padding:2px 8px; }}

/* 按钮（默认文字链接样式）*/
[data-testid="baseButton-secondary"] {{
    background:none !important; border:none !important; box-shadow:none !important;
    color:{TERTIARY_TEXT} !important; font-size:11px !important; padding:2px 0 !important;
    font-weight:400 !important; text-align:left !important; min-height:0 !important;
}}
[data-testid="baseButton-secondary"]:hover {{ color:{SECONDARY_TEXT} !important; text-decoration:underline; }}
[data-testid="baseButton-primary"] {{
    background:{PRIMARY_DARK} !important; color:{BG_CARD} !important;
    border:none !important; border-radius:8px !important; font-size:13px !important;
}}

/* 导航栏 */
.nb {{ background:{BG_CARD}; border:0.5px solid {BORDER}; border-radius:12px; height:52px;
       display:flex; align-items:center; padding:0 20px; margin-bottom:0; gap:6px; }}
.lo {{ width:24px; height:24px; background:{PRIMARY_DARK}; border-radius:5px; color:white;
       font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.bn {{ font-size:14px; font-weight:500; color:{PRIMARY_DARK}; }}
.bs {{ font-size:11px; color:{TERTIARY_TEXT}; margin-left:2px; }}
.av {{ width:28px; height:28px; background:{PRIMARY_DARK}; border-radius:50%; color:white;
       font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.sn {{ font-size:12px; color:{TERTIARY_TEXT}; }}

/* Fix 2：modal 内字号强制覆盖 */
[data-testid="stModal"] h1,
[data-testid="stModal"] h2,
[data-testid="stModal"] h3 {{
    font-size:15px !important; font-weight:600 !important;
    color:{PRIMARY_DARK} !important; margin:10px 0 4px !important;
}}
[data-testid="stModal"] p,
[data-testid="stModal"] li {{
    font-size:13px !important; line-height:1.7 !important;
}}
[data-testid="stModal"] strong {{ font-size:13px !important; font-weight:600 !important; }}
.modal-h1 {{ font-size:18px; font-weight:600; color:{PRIMARY_DARK}; margin:0 0 6px 0; }}

/* 聊天气泡 */
.chat-wrap {{ margin:8px 0; }}
.chat-label {{ font-size:11px; color:{TERTIARY_TEXT}; margin-bottom:2px; }}
.chat-label-r {{ text-align:right; }}
.chat-bubble-user {{
    background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:12px 12px 2px 12px;
    padding:8px 12px; font-size:12px; color:{PRIMARY_DARK}; display:inline-block;
    max-width:70%; line-height:1.6; float:right; clear:both;
}}
.chat-clear {{ clear:both; }}

/* st.tabs 覆盖 */
.stTabs [data-baseweb="tab-list"] {{
    gap:0; background:transparent; border-bottom:0.5px solid {BORDER}; margin-bottom:12px; padding:0;
}}
.stTabs [data-baseweb="tab"] {{
    font-size:13px; color:{TERTIARY_TEXT}; padding:8px 16px;
    border-bottom:1.5px solid transparent; background:transparent;
}}
.stTabs [aria-selected="true"] {{
    color:{PRIMARY_DARK} !important; font-weight:500; border-bottom:1.5px solid {PRIMARY_DARK} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding:0 !important; }}

/* 聊天输入框 */
[data-testid="stChatInput"] textarea {{
    background:{BG_CARD} !important; border:0.5px solid {BORDER} !important;
    border-radius:8px !important; font-size:12px !important; color:{PRIMARY_DARK} !important;
}}

/* V2 预览卡 */
.v2card {{ background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:8px; padding:16px; margin-bottom:8px; }}
</style>""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
os.makedirs(PROJECT_ROOT / "uploads", exist_ok=True)   # 商家上传图片目录

for _k, _v in [
    ("messages",           []),
    ("dialog_prompt",      None),
    ("dialog_title",       None),
    ("refresh_time",       "2026-06-06 06:00"),
    ("_nav_tab",           None),          # 用于 JS tab 跳转
    ("_vision_results",    []),            # Vision API 解析结果
    ("_vision_filenames",  []),            # 解析的文件名列表
    ("revenue_period",     "昨日"),        # 营收时间段选择
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─── API 客户端 ─────────────────────────────────────────────────────────────────
_key = os.getenv("ANTHROPIC_API_KEY", "")
if not _key:
    st.error("❌ 未找到 ANTHROPIC_API_KEY，请在 .env 文件中配置。")
    st.stop()
client = anthropic.Anthropic(api_key=_key)

# ─── 数据加载（Fix 8：支持刷新扰动）──────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    _df = pd.read_csv(path, encoding="utf-8-sig")
    _df["日期"] = pd.to_datetime(_df["日期"])
    return _df

_df_base = load_data(str(PROJECT_ROOT / "mock_data.csv"))

if "df_live" not in st.session_state:
    st.session_state.df_live = _df_base.copy()

dfl = st.session_state.df_live   # 全页面使用 dfl 而非 df

# ══════════════════════════════════════════════════════════════════════════════
# ▌数据分析引擎 —— 从 dfl 算出特征摘要，驱动巡检卡片和 prompt
# ══════════════════════════════════════════════════════════════════════════════
# 阈值（可调）
_ALERT_RED_THRESHOLD   = -0.25    # 近7天曝光环比下跌超过 25% → 红色预警
_ALERT_GREEN_THRESHOLD =  0.40    # 近7天曝光环比上涨超过 40% → 绿色机会
_ALERT_CVR_THRESHOLD   =  0.025   # 近30天转化率（下单/曝光）低于 2.5% → 黄色提醒


def compute_data_summary(df: pd.DataFrame) -> dict:
    """
    计算每个款式的数据特征：
    - 近7天 / 前7天 / 近30天 / 前30天 均值及环比
    - 转化率 CVR（下单/曝光）、点击率 CTR
    """
    today  = df["日期"].max()
    styles = df["款式名称"].unique()
    result = {}

    for style in styles:
        s = df[df["款式名称"] == style].sort_values("日期")

        # ── 时间窗口切片 ──────────────────────────────────────────────
        s7    = s[s["日期"] >= today - timedelta(days=6)]           # 近7天
        p7    = s[(s["日期"] >= today - timedelta(days=13)) &
                   (s["日期"] <  today - timedelta(days=6))]        # 前7天
        s30   = s[s["日期"] >= today - timedelta(days=29)]          # 近30天
        p30   = s[(s["日期"] >= today - timedelta(days=59)) &
                   (s["日期"] <  today - timedelta(days=29))]       # 前30天

        # ── 曝光均值 & 环比 ──────────────────────────────────────────
        exp7_avg  = s7["曝光数"].mean()  if len(s7)  > 0 else 0
        exp_p7    = p7["曝光数"].mean()  if len(p7)  > 0 else exp7_avg
        exp30_avg = s30["曝光数"].mean() if len(s30) > 0 else 0
        exp_p30   = p30["曝光数"].mean() if len(p30) > 0 else exp30_avg

        wow7  = (exp7_avg  - exp_p7)  / exp_p7  if exp_p7  > 0 else 0
        wow30 = (exp30_avg - exp_p30) / exp_p30 if exp_p30 > 0 else 0

        # ── 转化率 & 点击率 ──────────────────────────────────────────
        imp7   = s7["曝光数"].sum();  ord7 = s7["下单数"].sum();  clk7 = s7["点击数"].sum()
        imp30  = s30["曝光数"].sum(); ord30 = s30["下单数"].sum()

        cvr7   = ord7  / imp7  if imp7  > 0 else 0
        cvr30  = ord30 / imp30 if imp30 > 0 else 0
        ctr7   = clk7  / imp7  if imp7  > 0 else 0

        result[style] = {
            "exp7_avg":  round(exp7_avg,  1),
            "exp_p7":    round(exp_p7,    1),
            "exp30_avg": round(exp30_avg, 1),
            "wow7":      round(wow7,  4),      # 近7天 vs 前7天 曝光环比
            "wow30":     round(wow30, 4),
            "cvr7":      round(cvr7,  4),
            "cvr30":     round(cvr30, 4),
            "ctr7":      round(ctr7,  4),
            "orders30":  int(ord30),
            "aov30":     round(s30["客单价"].mean(), 1) if len(s30) > 0 else 0,
        }
    return result


def detect_patrol_alerts(summary: dict) -> list:
    """
    从数据特征里自动识别3张巡检卡片（红/绿/黄）
    规则：下跌>25%红、上涨>40%绿、CVR<2.5%黄；
    若无超阈值款式，取各维度最差/最好的款式仍显示卡片
    """
    styles = list(summary.keys())

    # ── 红：近7天曝光环比跌幅最大的款式 ─────────────────────────────
    red_s = min(styles, key=lambda s: summary[s]["wow7"])
    rm    = summary[red_s]
    exceeded_red = rm["wow7"] < _ALERT_RED_THRESHOLD
    red_tag  = "异常下滑" if exceeded_red else "关注提示"
    red_info = (
        f"近7天曝光日均 {int(rm['exp7_avg']):,}，"
        f"环比前7天 {rm['wow7']*100:+.0f}%<br>"
        f"近7天转化率 {rm['cvr7']*100:.1f}%"
    )
    red_prompt = (
        f"{red_s}近7天曝光日均 {int(rm['exp7_avg']):,} 次，"
        f"较前7天变化 {rm['wow7']*100:+.1f}%，"
        f"近7天转化率 {rm['cvr7']*100:.2f}%，近7天点击率 {rm['ctr7']*100:.2f}%。\n"
        "请给出：1）这个趋势最可能的 2-3 个成因及验证方法；"
        "2）在平台内立即执行的具体动作；3）预期恢复时间。"
    )

    # ── 绿：近7天曝光环比涨幅最大的款式 ─────────────────────────────
    grn_s = max(styles, key=lambda s: summary[s]["wow7"])
    gm    = summary[grn_s]
    exceeded_grn = gm["wow7"] > _ALERT_GREEN_THRESHOLD
    grn_tag  = "机会上升" if exceeded_grn else "相对稳健"
    grn_info = (
        f"近7天曝光日均 {int(gm['exp7_avg']):,}，"
        f"环比前7天 {gm['wow7']*100:+.0f}%<br>"
        f"近7天转化率 {gm['cvr7']*100:.1f}%"
    )
    grn_prompt = (
        f"{grn_s}近7天曝光日均 {int(gm['exp7_avg']):,} 次，"
        f"较前7天变化 {gm['wow7']*100:+.1f}%，"
        f"近7天转化率 {gm['cvr7']*100:.2f}%。\n"
        "请给出：1）上涨背后的用户需求分析；"
        "2）如何抓住窗口期加大推广（具体动作）；3）窗口期预计持续多久。"
    )

    # ── 黄：近30天 CVR 最低的款式 ──────────────────────────────────
    ylw_s = min(styles, key=lambda s: summary[s]["cvr30"])
    ym    = summary[ylw_s]
    exceeded_ylw = ym["cvr30"] < _ALERT_CVR_THRESHOLD
    ylw_tag  = "转化偏低" if exceeded_ylw else "转化留意"
    ylw_info = (
        f"近30天转化率 {ym['cvr30']*100:.1f}%"
        + (" (低于 2.5% 基准)" if exceeded_ylw else "（当前最低款式）") +
        f"<br>近7天点击率 {ym['ctr7']*100:.1f}%"
    )
    ylw_prompt = (
        f"{ylw_s}近30天转化率（下单/曝光）{ym['cvr30']*100:.2f}%，"
        f"近7天点击率 {ym['ctr7']*100:.2f}%，"
        f"近30天总下单 {ym['orders30']} 单。\n"
        "请给出：1）转化率偏低最可能的 2-3 个卡点；"
        "2）通过套餐结构/定价/首图调整提升转化的具体方案；3）合理的目标转化率。"
    )

    return [
        {"cls": "acR", "tcls": "aR", "tag": red_tag,
         "name": red_s,  "data": red_info,  "prompt": red_prompt},
        {"cls": "acG", "tcls": "aG", "tag": grn_tag,
         "name": grn_s,  "data": grn_info,  "prompt": grn_prompt},
        {"cls": "acY", "tcls": "aY", "tag": ylw_tag,
         "name": ylw_s,  "data": ylw_info,  "prompt": ylw_prompt},
    ]


def build_data_context(df: pd.DataFrame, summary: dict) -> str:
    """
    把数据特征摘要转为结构化文字，用于拼接 Agent prompt
    """
    today = df["日期"].max()
    lines = [
        f"以下是店铺近期经营数据摘要（数据截至 {today.strftime('%Y-%m-%d')}）：\n",
        "【近 7 天各款式数据（均值，以及与前7天的曝光环比）】",
        f"{'款式':<10} {'7天均曝光':>9}  {'7天环比':>8}  {'7天CVR':>7}  {'7天CTR':>7}",
        "─" * 52,
    ]
    for style, m in sorted(summary.items(), key=lambda x: x[1]["wow7"]):
        lines.append(
            f"{style:<10} {int(m['exp7_avg']):>9,}  "
            f"{m['wow7']*100:>+7.1f}%  "
            f"{m['cvr7']*100:>6.2f}%  "
            f"{m['ctr7']*100:>6.2f}%"
        )
    lines += [
        "",
        "【近 30 天各款式数据（均值，以及与前30天的环比）】",
        f"{'款式':<10} {'30天均曝光':>10}  {'30天环比':>8}  {'30天CVR':>8}  {'总下单':>6}  {'均客单':>7}",
        "─" * 58,
    ]
    for style, m in sorted(summary.items(), key=lambda x: x[1]["wow30"]):
        lines.append(
            f"{style:<10} {int(m['exp30_avg']):>10,}  "
            f"{m['wow30']*100:>+7.1f}%  "
            f"{m['cvr30']*100:>7.2f}%  "
            f"{m['orders30']:>6}  "
            f"¥{m['aov30']:>6.0f}"
        )
    # 异常标注
    anomalies = []
    for style, m in summary.items():
        if m["wow7"]  < _ALERT_RED_THRESHOLD:
            anomalies.append(f"- {style}：近7天曝光环比 {m['wow7']*100:.0f}%（触发红色预警 >25% 下跌）")
        if m["wow7"]  > _ALERT_GREEN_THRESHOLD:
            anomalies.append(f"- {style}：近7天曝光环比 +{m['wow7']*100:.0f}%（触发绿色机会 >40% 上涨）")
        if m["cvr30"] < _ALERT_CVR_THRESHOLD:
            anomalies.append(f"- {style}：近30天CVR {m['cvr30']*100:.1f}%（触发黄色提醒 <2.5%）")
    lines += (
        ["", "【系统识别到的异常】"] + anomalies
        if anomalies else
        ["", "【异常检测结果】", "- 当前各款式数据无明显超阈值异常，整体相对平稳"]
    )
    return "\n".join(lines)


# ── 在页面加载时计算一次，全局可用 ─────────────────────────────────────────
_ds     = compute_data_summary(dfl)        # 数据特征摘要
_patrol = detect_patrol_alerts(_ds)        # 3 张动态预警卡片

# ══════════════════════════════════════════════════════════════════════════════
# ▌Fix 3：@st.dialog（Fix 3 max_tokens=8000，Fix 4 不保存到聊天历史）
# ══════════════════════════════════════════════════════════════════════════════
@st.dialog("甲心助手分析", width="large")
def show_analysis_dialog():
    prompt_text = st.session_state.dialog_prompt
    title_text  = st.session_state.dialog_title
    if not prompt_text:
        st.session_state.dialog_prompt = None
        return

    # Fix 2.1：标题 18px 加粗（用 HTML 而非 markdown heading，避免被 CSS 统一覆盖）
    st.markdown(f'<div class="modal-h1">{title_text}</div>', unsafe_allow_html=True)
    st.divider()

    def _stream():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,              # Fix 3
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_text}],
        ) as _s:
            yield from _s.text_stream

    # Fix 4：只在 modal 内输出，不保存到 messages（防止聊天区重复渲染）
    st.write_stream(_stream())
    st.session_state.dialog_prompt = None


def trigger_dialog(prompt: str, title: str):
    st.session_state.dialog_prompt = prompt
    st.session_state.dialog_title  = title
    st.rerun()


# ─── 巡检报告 prompt 生成（使用真实数据特征摘要）──────────────────────────────
def _build_full_report_prompt() -> str:
    data_ctx = build_data_context(dfl, _ds)
    return (
        "你是甲心助手，请基于以下店铺数据分析趋势并给出运营建议。\n\n"
        f"{data_ctx}\n\n"
        "请按八段式结构输出完整分析：\n"
        "诊断假设 / 数据观察 / 趋势判断 / 用户洞察 / 运营建议 / 不建议做什么 / 风险提示 / 下一步建议\n\n"
        "关键要求：\n"
        "- 必须基于上面提供的真实数据进行分析，不要编造任何数字\n"
        "- 如果数据中没有明显异常，直接说'数据相对平稳'，不要硬找问题\n"
        "- 建议要包含具体数字和可执行的步骤\n"
        "- 在数据观察中，每个款式必须引用表格里的具体数值"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ▌Sidebar：数据真相页面（仅供评测，演示时对照 Agent 分析准确性）
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f'<div style="font-size:11px;color:{TERTIARY_TEXT};padding:8px 0 4px;">甲心助手 · 内部工具</div>',
        unsafe_allow_html=True,
    )
    _show_truth = st.checkbox("📊 数据真相（评测用）", value=False)

    if _show_truth:
        try:
            with open(PROJECT_ROOT / "mock_data_truth.json", encoding="utf-8") as _f:
                _truth = json.load(_f)

            st.markdown(f"""
            <div style="font-size:12px;font-weight:600;color:{PRIMARY_DARK};
                        margin:8px 0 4px;">真实参数（Agent 看不到）</div>
            """, unsafe_allow_html=True)

            _style_keys = [k for k in _truth if not k.startswith("_")]
            for _sty in _style_keys:
                _t  = _truth[_sty]
                _sl = _t["trend_slope"]
                _dot = (f'<span style="color:{GREEN_ACCENT}">▲</span>'
                        if _sl > 0.005 else
                        f'<span style="color:{RED_ACCENT}">▼</span>'
                        if _sl < -0.005 else
                        f'<span style="color:{TERTIARY_TEXT}">─</span>')
                st.markdown(f"""
                <div style="background:{BG_BASE};border:0.5px solid {BORDER};border-radius:6px;
                            padding:8px 10px;margin-bottom:6px;font-size:11px;">
                    <b style="font-size:12px;">{_sty}</b> {_dot}
                    <span style="float:right;font-size:10px;color:{TERTIARY_TEXT};">{_t['interpretation']}</span><br>
                    slope = <code>{_sl:+.4f}</code><br>
                    曝光基准 {int(_t['base_exposure']):,} · CTR {_t['base_ctr']:.1%} · CVR {_t['base_cvr']:.1%}
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="font-size:12px;font-weight:600;color:{PRIMARY_DARK};margin:10px 0 4px;">
                随机异常事件
            </div>""", unsafe_allow_html=True)
            for _ev in _truth.get("_random_events", {}).get("spikes", []):
                st.markdown(
                    f'<div style="font-size:11px;color:{GREEN_ACCENT};">'
                    f'↑ 突涨 {_ev["date"]} {_ev["style"]}</div>', unsafe_allow_html=True)
            for _ev in _truth.get("_random_events", {}).get("dips", []):
                st.markdown(
                    f'<div style="font-size:11px;color:{RED_ACCENT};">'
                    f'↓ 突跌 {_ev["date"]} {_ev["style"]}</div>', unsafe_allow_html=True)

            st.divider()
            st.markdown(
                f'<div style="font-size:10px;color:{TERTIARY_TEXT};">'
                f'此页面仅用于 Agent 评测，演示时对照分析准确性</div>',
                unsafe_allow_html=True)

        except FileNotFoundError:
            st.warning("未找到 mock_data_truth.json\n请先运行 generate_mock_data.py")

# ══════════════════════════════════════════════════════════════════════════════
# ▌区域 1：顶部导航栏
# ══════════════════════════════════════════════════════════════════════════════
_store_name = "XXX美甲美睫 · 徐家汇店"

# ── 改造5：演示价值说明条 ──────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(90deg,{BG_BASE} 0%,#EBF0F5 100%);
            border:0.5px solid {BORDER};border-radius:8px;padding:9px 16px;
            margin-bottom:8px;font-size:11px;color:{SECONDARY_TEXT};line-height:1.7;">
    <span style="font-weight:600;color:{PRIMARY_DARK};">V2 真飞轮：</span>
    商家上传作品 → AI 自动打标签 → 心智 DNA 演化 → 所有 Agent 建议自动适配本店风格。
    试试在 <b>UGC 中心 → 商家内容池</b> 上传几张你的美甲图，看 AI 如何理解你的店。
</div>""", unsafe_allow_html=True)

# ── Bug 1：JS tab 跳转（点"详见 UGC 中心"后触发）──────────────────────────────
if st.session_state.get("_nav_tab") is not None:
    _tidx = st.session_state._nav_tab
    st.session_state._nav_tab = None
    st.components.v1.html(f"""<script>
    setTimeout(function(){{
        var t=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        if(t&&t.length>{_tidx})t[{_tidx}].click();
    }},350);
    </script>""", height=0)

# ── navbar: logo + brand + 门店名
nb_l, nb_r = st.columns([5, 5])
with nb_l:
    st.markdown(f"""
    <div class="nb" style="border-radius:12px 0 0 12px;border-right:none;">
        <div class="lo">甲</div>
        <span class="bn" style="margin-left:8px;">甲心助手</span>
        <span class="bs">美业商家 AI 运营平台</span>
        <span class="sn" style="margin-left:auto;">{_store_name}</span>
    </div>""", unsafe_allow_html=True)

with nb_r:
    # 右侧：日期戳 + 刷新按钮 + 铃铛 popover + 头像
    st.markdown(f"""
    <div class="nb" style="border-radius:0 12px 12px 0;gap:10px;justify-content:flex-end;">
        <span style="font-size:11px;color:{TERTIARY_TEXT};">
            数据更新于 {st.session_state.refresh_time}
        </span>
    </div>""", unsafe_allow_html=True)

# 刷新按钮 + 铃铛 popover + 头像（置于右列下方，紧贴导航栏）
_, act_c1, act_c2, act_c3 = st.columns([8, 0.6, 0.8, 0.6])

with act_c1:
    # Fix 8：刷新按钮
    if st.button("↻", key="refresh_btn", help="拉取最新数据"):
        with st.spinner("正在拉取最新数据…"):
            time.sleep(1)
            df_new = st.session_state.df_live.copy()
            last_date = df_new["日期"].max()
            mask = df_new["日期"] == last_date
            n = int(mask.sum())
            for _col in ["曝光数", "点击数", "收藏数", "下单数"]:
                df_new.loc[mask, _col] = (
                    df_new.loc[mask, _col].values *
                    (1 + np.random.uniform(-0.05, 0.05, n))
                ).clip(0).round(0).astype(int)
            st.session_state.df_live = df_new
            st.session_state.refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        dfl = st.session_state.df_live
        st.toast("✅ 数据已更新")
        st.rerun()

with act_c2:
    # 铃铛 popover：动态显示 _patrol 里的实际预警
    _bell_colors = {"acR": RED_ACCENT, "acG": GREEN_ACCENT, "acY": YELLOW_ACCENT}
    with st.popover("🔔 3"):
        st.markdown(f"**今日预警（{len(_patrol)} 条）**")
        st.markdown("---")
        for _pa in _patrol:
            _bc  = _bell_colors.get(_pa["cls"], TERTIARY_TEXT)
            _btx = f"{_pa['name']} · {_pa['tag']}"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:6px 0;
                        border-bottom:0.5px solid {BORDER};">
                <div style="width:8px;height:8px;border-radius:50%;background:{_bc};flex-shrink:0;"></div>
                <span style="font-size:12px;color:{SECONDARY_TEXT};flex:1;">{_btx}</span>
                <span style="font-size:10px;color:{TERTIARY_TEXT};">06:00</span>
            </div>""", unsafe_allow_html=True)

with act_c3:
    st.markdown(f'<div class="av" style="margin-top:6px;">商</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Fix 1：st.tabs 为唯一 tab 控件（HTML navbar 不含 tab 名称）
# ══════════════════════════════════════════════════════════════════════════════
# ── 指标卡片 HTML 渲染（module级，tabs[0]/tabs[1]/tabs[6] 共用）──────────────────
def _mc(label, value, change, direction, benchmark=""):
    _cls = {"up": "up", "down": "dn", "flat": "fl"}[direction]
    _bm  = f'<div class="mc3">{benchmark}</div>' if benchmark else ""
    return (f'<div class="mc"><div class="ml">{label}</div>'
            f'<div class="mv">{value}</div>'
            f'<div class="mc2 {_cls}">{change}</div>{_bm}</div>')

# ── UGC 数据加载（含缓存）────────────────────────────────────────────────────
@st.cache_data
def load_ugc_ext(path: str) -> pd.DataFrame:
    _d = pd.read_csv(path, encoding="utf-8-sig")
    _d["日期"] = pd.to_datetime(_d["日期"])
    return _d

@st.cache_data
def load_ugc_int(path: str) -> dict:
    with open(path, encoding="utf-8") as _f:
        return json.load(_f)


# ── 内容池工具函数 ────────────────────────────────────────────────────────────
def _load_content_pool() -> list:
    try:
        with open(PROJECT_ROOT / "content_pool.json", encoding="utf-8") as _f:
            return json.load(_f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_to_content_pool(new_entries: list):
    pool = _load_content_pool()
    pool.extend(new_entries)
    with open(PROJECT_ROOT / "content_pool.json", "w", encoding="utf-8") as _f:
        json.dump(pool, _f, ensure_ascii=False, indent=2)


def _call_vision_api(uploaded_files: list, cl) -> list:
    """调用 Claude Vision API，返回解析后的标签列表（每张图一项）"""
    content = []
    for _uf in uploaded_files[:5]:
        _uf.seek(0)
        _b64 = base64.b64encode(_uf.read()).decode("utf-8")
        _mt  = "image/jpeg" if _uf.name.lower().endswith(("jpg","jpeg")) else "image/png"
        content.append({"type": "image",
                         "source": {"type": "base64", "media_type": _mt, "data": _b64}})
    content.append({"type": "text", "text": (
        "你是美甲行业的视觉分析师。请分析这些美甲图片，对每张图输出 JSON：\n"
        "{\n"
        '  "图片编号": 1,\n'
        '  "款式类型": "猫眼/法式/手绘/纯色/穿戴甲/果冻甲/其他",\n'
        '  "主色系": "颜色描述（约 5-10 字）",\n'
        '  "风格标签": ["从这些中选 2-3 个：简约/华丽/复古/纯欲/可爱/高级/通勤/约会"],\n'
        '  "工艺难度": "低/中/高",\n'
        '  "适合人群": "20-25 字描述",\n'
        '  "推荐定价区间": "整数范围，单位元"\n'
        "}\n"
        "多张图请输出 JSON 数组，每张图一个对象。\n"
        "要求：必须基于图片视觉特征客观判断，不要编造。"
    )})
    resp = cl.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": content}]
    )
    raw  = resp.content[0].text
    m    = re.search(r"\[.*\]|\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"无法解析 Vision 输出：{raw[:200]}")
    parsed = json.loads(m.group(0))
    return parsed if isinstance(parsed, list) else [parsed]


tabs = st.tabs(["总览", "营收", "流量", "推广", "顾客", "商品", "UGC 中心"])

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 0 "总览" —— 所有现有内容
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:

    # ── 今日巡检（使用动态计算的 _patrol，非硬编码）──────────────────────────────
    with st.container(border=True):
        _h, _r = st.columns([3, 1])
        with _h:
            _n_alerts = len(_patrol)
            st.markdown(f"""
            <div class="sh" style="margin-bottom:12px;">
                <span class="stt">甲心助手 · 今日巡检</span>
                <span class="ss">已扫描 {len(_ds)} 个款式 · {_n_alerts} 条异常 · 06:00 自动生成</span>
            </div>""", unsafe_allow_html=True)
        with _r:
            if st.button("查看完整报告 →", key="full_report"):
                trigger_dialog(_build_full_report_prompt(), "今日运营巡检报告")

        pc1, pc2, pc3 = st.columns(3, gap="small")
        for _col, _a in zip([pc1, pc2, pc3], _patrol):
            with _col:
                st.markdown(f"""
                <div class="ac {_a['cls']}">
                    <div class="act {_a['tcls']}">{_a['tag']}</div>
                    <div class="an">{_a['name']}</div>
                    <div class="ad">{_a['data']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("让甲心助手解读 →", key=f"pa_{_a['name']}"):
                    trigger_dialog(_a["prompt"], f"解读预警：{_a['name']}")

    # ── 改造2：内容资产信号（从 content_pool.json 动态触发）────────────────────
    _cp_sig_pool = _load_content_pool()
    if _cp_sig_pool:
        _sty_ct, _diff_ct = {}, {}
        for _pe in _cp_sig_pool:
            _pt = _pe.get("analysis", {}).get("款式类型", "其他")
            _pd = _pe.get("analysis", {}).get("工艺难度", "中")
            _sty_ct[_pt] = _sty_ct.get(_pt, 0) + 1
            _diff_ct[_pd] = _diff_ct.get(_pd, 0) + 1
        _sig_cards = []
        for _sty, _cnt in _sty_ct.items():
            if _cnt >= 5:
                _sig_cards.append(f"你已沉淀 {_cnt} 张{_sty}图，可作为引流首图候选")
        for _sty2 in _sty_ct:
            _hc = sum(1 for _pe in _cp_sig_pool
                      if _pe.get("analysis",{}).get("款式类型")==_sty2
                      and _pe.get("analysis",{}).get("工艺难度")=="高")
            if _hc >= 3:
                _sig_cards.append(f"你的{_sty2}工艺壁垒已建立（{_hc} 张高难度），可推拔升款套餐")
        if len(_cp_sig_pool) >= 20:
            _sig_cards.append(f"内容资产已达 {len(_cp_sig_pool)} 张，建议开通「作品集首图轮播」功能")
        if _sig_cards:
            with st.container(border=True):
                st.markdown(f"""
                <div class="sh" style="margin-bottom:10px;">
                    <span class="stt">📡 内容资产信号</span>
                    <span class="ss">基于商家上传内容自动触发</span>
                </div>""", unsafe_allow_html=True)
                for _sc in _sig_cards:
                    st.markdown(f"""
                    <div style="background:#EBF0F5;border:0.5px solid {BORDER};
                                border-left:2px solid {BLUE_ACCENT};border-radius:8px;
                                padding:10px 14px;margin-bottom:6px;font-size:13px;
                                color:{SECONDARY_TEXT};">{_sc}</div>
                    """, unsafe_allow_html=True)

    # ── Bug 3：营收概览（时间段真实切换）──────────────────────────────────────
    with st.container(border=True):
        _rh, _rp = st.columns([4, 2])
        with _rh:
            st.markdown(f"""
            <div style="font-size:14px;font-weight:500;color:{PRIMARY_DARK};padding-top:5px;">
                营收概览</div>
            <div style="font-size:11px;color:{TERTIARY_TEXT};">数据更新于今日 06:00</div>
            """, unsafe_allow_html=True)
        with _rp:
            _rp_sel = st.segmented_control(
                "时间范围", ["昨日", "近7日", "近30日"],
                key="revenue_period", label_visibility="collapsed"
            ) or "昨日"

        # 根据选择计算数据
        _rtd = dfl["日期"].max()
        if _rp_sel == "近7日":
            _rdf  = dfl[dfl["日期"] >= _rtd - timedelta(days=6)]
            _rpdf = dfl[(dfl["日期"] >= _rtd - timedelta(days=13)) &
                        (dfl["日期"] <  _rtd - timedelta(days=6))]
            _rcomp = "比前7日"
        elif _rp_sel == "近30日":
            _rdf  = dfl[dfl["日期"] >= _rtd - timedelta(days=29)]
            _rpdf = dfl[(dfl["日期"] >= _rtd - timedelta(days=59)) &
                        (dfl["日期"] <  _rtd - timedelta(days=29))]
            _rcomp = "比前30日"
        else:   # 昨日
            _rdf  = dfl[dfl["日期"] == _rtd]
            _rpdf = dfl[dfl["日期"] == _rtd - timedelta(days=1)]
            _rcomp = "比前日"

        _rev_t = (_rdf["下单数"] * _rdf["客单价"]).sum()
        _rev_y = (_rpdf["下单数"] * _rpdf["客单价"]).sum()
        _rev_c = (_rev_t - _rev_y) / _rev_y * 100 if _rev_y else 0
        _ord_t = int(_rdf["下单数"].sum())
        _ord_y = int(_rpdf["下单数"].sum())
        _imp_t = _rdf["曝光数"].sum()
        _cvr_t = _ord_t / _imp_t * 100 if _imp_t else 0
        _cvr_y = _rpdf["下单数"].sum() / _rpdf["曝光数"].sum() * 100 if _rpdf["曝光数"].sum() else 0
        _aov_t = _rev_t / _ord_t if _ord_t else 0

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _m1, _m2, _m3, _m4 = st.columns(4, gap="small")
        _m1.markdown(_mc("营业收入", f"¥{int(_rev_t):,}",
                         f"{'↑' if _rev_c>0 else '↓'} {abs(_rev_c):.0f}% {_rcomp}",
                         "up" if _rev_c>0 else "down", "商圈均值 ¥6,420"), unsafe_allow_html=True)
        _m2.markdown(_mc("订单量", str(_ord_t),
                         f"{'↑' if _ord_t>_ord_y else '↓'} {abs(_ord_t-_ord_y)} 单 {_rcomp}",
                         "up" if _ord_t>_ord_y else "down", "商圈均值 38 单"), unsafe_allow_html=True)
        _m3.markdown(_mc("转化率", f"{_cvr_t:.1f}%",
                         f"{'↑' if _cvr_t>_cvr_y else '↓'} {abs(_cvr_t-_cvr_y):.1f}% {_rcomp}",
                         "up" if _cvr_t>_cvr_y else "down", "商圈均值 3.1%"), unsafe_allow_html=True)
        _m4.markdown(_mc("客单价", f"¥{int(_aov_t)}", "持平", "flat", "商圈均值 ¥198"),
                     unsafe_allow_html=True)

    # ── 热度折线图 ───────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div class="sh">
            <span class="stt">门店主打款热度（近 7 日）</span>
            <span class="updt">数据更新于今日 06:00</span>
        </div>
        <div class="lgrow">
            <span class="lg"><span class="lgl" style="background:{RED_ACCENT}"></span>猫眼（主打1）</span>
            <span class="lg"><span class="lgl" style="background:{GREEN_ACCENT}"></span>纯欲风（主打2）</span>
            <span class="lg"><span class="lgl" style="background:{BLUE_ACCENT}"></span>法式（主打3）</span>
            <span class="lg"><span class="lgd"></span>商圈均值</span>
        </div>""", unsafe_allow_html=True)

        _x7 = ["5/31", "6/1", "6/2", "6/3", "6/4", "6/5", "6/6"]
        _trend_lines = {
            "猫眼":    ([85,82,78,74,70,66,62], RED_ACCENT,  "solid"),
            "纯欲风":  ([32,38,45,52,59,65,72], GREEN_ACCENT,"solid"),
            "法式":    ([55,57,53,56,55,54,56], BLUE_ACCENT, "solid"),
            "商圈均值":([60,59,58,57,57,56,55], "#C0BDBA",  "dash"),
        }
        _fig = go.Figure()
        for _nm, (_vals, _col, _dash) in _trend_lines.items():
            _fig.add_trace(go.Scatter(
                x=_x7, y=_vals, name=_nm, mode="lines", showlegend=False,
                line=dict(color=_col, dash=_dash, width=1.5 if _dash=="solid" else 1.2),
            ))
        _fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=180, margin=dict(l=38, r=8, t=4, b=10),
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color=TERTIARY_TEXT), linecolor=BORDER),
            yaxis=dict(tickvals=[25,55,85], ticktext=["低","中","高"], showgrid=True,
                       gridcolor=BORDER, gridwidth=0.5, tickfont=dict(size=10, color=TERTIARY_TEXT),
                       range=[0,100]),
        )
        st.plotly_chart(_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"""
        <div class="ib">
            <strong style="color:{PRIMARY_DARK}">甲心助手解读：</strong>
            猫眼跑输商圈大盘（灰虚线），7 日内持续走弱；纯欲风跑赢大盘，涨幅明显。
            建议将猫眼从首图第一位下调，纯欲风升至首图，预计带动点击量提升 10–15%。
        </div>""", unsafe_allow_html=True)

    # ── 精简行业趋势预警条（数据来自 ugc_external.csv，详情见 UGC 中心 tab）──────
    # ── Bug 1 & 2：精简行业趋势条（字号提升、加色条、按钮可跳转）──────────────
    _trend_text = "正在加载行业 Top 信号…"
    try:
        _ugc_p = load_ugc_ext(str(PROJECT_ROOT / "ugc_external.csv"))
        _ud    = _ugc_p["日期"].max()
        _ur30  = (_ugc_p[_ugc_p["日期"] >= _ud - timedelta(days=29)]
                  .groupby("款式名")["笔记数"].sum())
        _up30  = (_ugc_p[(_ugc_p["日期"] >= _ud - timedelta(days=59)) &
                          (_ugc_p["日期"] <  _ud - timedelta(days=29))]
                  .groupby("款式名")["笔记数"].sum())
        _uchg  = ((_ur30 - _up30) / _up30 * 100).dropna().sort_values(ascending=False)
        _top2  = " · ".join(f"{s} ↑{v:.0f}%" for s, v in _uchg.head(2).items())
        _trend_text = f"本周行业 Top 信号：{_top2}"
    except Exception:
        pass

    _tb_l, _tb_r = st.columns([5, 1])
    with _tb_l:
        st.markdown(f"""
        <div style="background:{BG_BASE};border:0.5px solid {BORDER};
                    border-left:3px solid {TERTIARY_TEXT};border-radius:8px;
                    padding:10px 16px;font-size:14px;font-weight:500;color:{PRIMARY_DARK};
                    display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <span style="width:8px;height:8px;border-radius:50%;
                         background:{GREEN_ACCENT};flex-shrink:0;"></span>
            {_trend_text}
        </div>""", unsafe_allow_html=True)
    with _tb_r:
        if st.button("详见 UGC 中心 →", key="nav_ugc_btn"):
            st.session_state._nav_tab = 6
            st.rerun()
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── 问甲心助手 ───────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <div class="sh" style="margin-bottom:10px;">
            <span class="stt">问甲心助手</span>
            <span class="ss">你的专属运营顾问</span>
        </div>""", unsafe_allow_html=True)

        for _msg in st.session_state.messages:
            _txt = _msg.get("display", _msg["content"])
            if _msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-wrap">
                    <div class="chat-label chat-label-r">你</div>
                    <div class="chat-bubble-user">{_txt}</div>
                    <div class="chat-clear"></div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-label">甲心助手</div>', unsafe_allow_html=True)
                st.markdown(_txt)
                st.markdown('<div class="chat-clear"></div>', unsafe_allow_html=True)

        def stream_jiaxin(question: str):
            _hist = [{"role": m["role"], "content": m["content"]}
                     for m in st.session_state.messages]
            _hist.append({"role": "user", "content": question})
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=8000,          # Fix 3
                system=SYSTEM_PROMPT,
                messages=_hist,
            ) as _s:
                yield from _s.text_stream

        _user_input = st.chat_input("问甲心助手任何运营问题…")
        if _user_input:
            st.markdown(f"""
            <div class="chat-wrap">
                <div class="chat-label chat-label-r">你</div>
                <div class="chat-bubble-user">{_user_input}</div>
                <div class="chat-clear"></div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="chat-label">甲心助手</div>', unsafe_allow_html=True)
            with st.spinner("思考中…"):
                _reply = st.write_stream(stream_jiaxin(_user_input))
            st.session_state.messages.extend([
                {"role": "user",      "content": _user_input, "display": _user_input},
                {"role": "assistant", "content": _reply},
            ])

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 1 "营收" —— Fix 9：真实内容
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    # 30 天汇总指标
    _rev30 = (dfl["下单数"] * dfl["客单价"]).sum()
    _ord30 = int(dfl["下单数"].sum())
    _aov30 = _rev30 / _ord30 if _ord30 else 0

    with st.container(border=True):
        st.markdown('<div class="sh"><span class="stt">营收概览（近 30 天）</span></div>',
                    unsafe_allow_html=True)
        _rc1, _rc2, _rc3, _rc4 = st.columns(4, gap="small")
        _rc1.markdown(_mc("总营收", f"¥{int(_rev30):,}", "↑ 5.4% vs 商圈", "up", "商圈均值 ¥118,200"),
                      unsafe_allow_html=True)
        _rc2.markdown(_mc("订单总数", f"{_ord30} 单", "↑ 5.5% vs 商圈", "up", "商圈均值 580 单"),
                      unsafe_allow_html=True)
        _rc3.markdown(_mc("平均客单价", f"¥{int(_aov30)}", "高出商圈 3%", "up", "商圈均值 ¥198"),
                      unsafe_allow_html=True)
        _rc4.markdown(_mc("复购率", "32%", "↑ 4pct vs 商圈", "up", "商圈均值 28%"),
                      unsafe_allow_html=True)

    # 30 天营收趋势折线图
    with st.container(border=True):
        st.markdown('<div class="sh"><span class="stt">近 30 天营收趋势</span></div>',
                    unsafe_allow_html=True)
        _rev_by_day = dfl.groupby("日期").apply(
            lambda x: (x["下单数"] * x["客单价"]).sum()
        ).reset_index(name="营收")
        _district_avg = (_rev_by_day["营收"] * np.random.uniform(0.90, 0.98,
                         len(_rev_by_day))).round(0)

        _fig_rev = go.Figure()
        _fig_rev.add_trace(go.Scatter(
            x=_rev_by_day["日期"], y=_rev_by_day["营收"],
            name="本店", mode="lines",
            line=dict(color=RED_ACCENT, width=2),
        ))
        _fig_rev.add_trace(go.Scatter(
            x=_rev_by_day["日期"], y=_district_avg,
            name="商圈均值", mode="lines",
            line=dict(color="#C0BDBA", dash="dash", width=1.2),
        ))
        _fig_rev.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=220, margin=dict(l=50, r=10, t=10, b=30),
            legend=dict(orientation="h", x=0, y=1.15, font=dict(size=11, color=SECONDARY_TEXT)),
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color=TERTIARY_TEXT), linecolor=BORDER),
            yaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=0.5,
                       tickfont=dict(size=10, color=TERTIARY_TEXT), tickprefix="¥"),
        )
        st.plotly_chart(_fig_rev, use_container_width=True, config={"displayModeBar": False})

    # 分时段营收柱状图
    with st.container(border=True):
        st.markdown('<div class="sh"><span class="stt">分时段营收分布</span></div>',
                    unsafe_allow_html=True)
        _time_slots = ["上午 9–12 时", "下午 12–15 时", "下午 15–18 时", "晚间 18–21 时"]
        _slot_rev   = [18200, 32400, 38600, 28100]
        _colors_bar = [BG_BASE, RED_ACCENT, RED_ACCENT, BG_BASE]
        _fig_bar = go.Figure(go.Bar(
            x=_time_slots, y=_slot_rev,
            marker_color=[RED_ACCENT, GREEN_ACCENT, RED_ACCENT, BLUE_ACCENT],
            text=[f"¥{v:,}" for v in _slot_rev],
            textposition="outside",
            textfont=dict(size=11, color=SECONDARY_TEXT),
        ))
        _fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=200, margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(showgrid=False, tickfont=dict(size=11, color=SECONDARY_TEXT)),
            yaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=0.5,
                       tickfont=dict(size=10, color=TERTIARY_TEXT), tickprefix="¥"),
            showlegend=False,
        )
        st.plotly_chart(_fig_bar, use_container_width=True, config={"displayModeBar": False})

    st.markdown(f"""
    <div class="ib">
        营收模块支持多维度营收分析、商圈对标、时段拆解。
        甲心助手会基于营收异常自动触发巡检并生成调整建议。
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 2 "流量" —— Fix 9：V2 规划预览
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    with st.container(border=True):
        st.markdown(f"""
        <div style="padding:8px 0 16px 0;">
            <div style="font-size:18px;font-weight:600;color:{PRIMARY_DARK};">
                V2 即将上线 · 流量分析
            </div>
            <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:4px;">规划预览</div>
        </div>""", unsafe_allow_html=True)

        for _f in [
            "流量来源拆解（自然搜索 / 推广 / 推荐 / 直接访问占比分析）",
            "高价值流量入口识别与权重评估",
            "流量漏斗诊断（曝光 → 点击 → 进店 → 下单 全链路）",
            "跨平台流量对比（美团 / 大众点评 / 小红书 / 抖音）",
        ]:
            st.markdown(f"- {_f}")

        st.markdown(f"""
        <div class="ib" style="margin-top:16px;">
            流量模块帮助商家看清每一个进店用户从哪里来、为什么来、为什么没下单。
            甲心助手基于流量漏斗数据，精准定位卡点并给出可执行的提效建议。
        </div>
        <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:12px;">
            预计 V2.0 上线时间：2026 Q3
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 3 "推广" —— Fix 9：V2 规划预览
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    with st.container(border=True):
        st.markdown(f"""
        <div style="padding:8px 0 16px 0;">
            <div style="font-size:18px;font-weight:600;color:{PRIMARY_DARK};">
                V2 即将上线 · 推广管理
            </div>
            <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:4px;">规划预览</div>
        </div>""", unsafe_allow_html=True)

        for _f in [
            "多渠道推广计划管理（CPC / CPM / CPA 全类型）",
            "投放 ROI 实时监控与异常预警",
            "AI 智能竞价建议（基于历史转化数据）",
            "关键词热度趋势分析与出价优化",
        ]:
            st.markdown(f"- {_f}")

        st.markdown(f"""
        <div class="ib" style="margin-top:16px;">
            推广模块让商家在多个平台的投放预算一目了然，
            甲心助手结合转化数据给出智能竞价策略，让每一分推广费产生最大价值。
        </div>
        <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:12px;">
            预计 V2.0 上线时间：2026 Q3
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 4 "顾客" —— Fix 9：V2 规划预览
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    with st.container(border=True):
        st.markdown(f"""
        <div style="padding:8px 0 16px 0;">
            <div style="font-size:18px;font-weight:600;color:{PRIMARY_DARK};">
                V2 即将上线 · 顾客运营
            </div>
            <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:4px;">规划预览</div>
        </div>""", unsafe_allow_html=True)

        for _f in [
            "RFM 客户分层模型（最近消费 / 消费频次 / 消费金额）",
            "自动化客户分群与标签体系",
            "沉睡客户唤回工作流（30 天 / 60 天分级预警）",
            "老客户 LTV 预测与高价值客群画像",
        ]:
            st.markdown(f"- {_f}")

        st.markdown(f"""
        <div class="ib" style="margin-top:16px;">
            顾客模块从"一次性流量"走向"长期资产"——
            甲心助手自动识别沉睡客户并生成唤回话术，帮助商家将复购率从行业均值 28% 提升到 35% 以上。
        </div>
        <div style="font-size:11px;color:{TERTIARY_TEXT};margin-top:12px;">
            预计 V2.0 上线时间：2026 Q3
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 5 "商品" —— Fix 9：真实内容（款式表格）
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    with st.container(border=True):
        st.markdown('<div class="sh"><span class="stt">在售款式一览</span></div>',
                    unsafe_allow_html=True)

        _df_prod = pd.DataFrame({
            "款式名称":   ["猫眼款", "纯欲风", "法式精修", "穿戴甲套餐", "手绘油画风"],
            "类型":       ["主力款",  "引流款",  "主力款",   "引流款",    "拔升款"],
            "定价":       ["¥298",   "¥168",   "¥358",    "¥111",     "¥488"],
            "近30天销量": [142,       98,        76,         89,          24],
            "库存状态":   ["充足",    "充足",    "充足",     "库存紧张",  "充足"],
            "趋势":       ["↓",      "↑",       "→",        "↑",         "↑"],
        })

        # 用 st.dataframe 渲染（支持滚动、排序）
        st.dataframe(
            _df_prod,
            use_container_width=True,
            hide_index=True,
            column_config={
                "款式名称": st.column_config.TextColumn("款式名称", width="medium"),
                "近30天销量": st.column_config.NumberColumn("近30天销量", format="%d 单"),
                "趋势": st.column_config.TextColumn("30天趋势", width="small"),
            },
        )

    st.markdown(f"""
    <div class="ib">
        商品模块支持款式上下架管理、定价策略优化、库存预警与款式生命周期分析。
        甲心助手基于销量趋势自动提示"需要补库存"或"建议下架"的款式。
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Tab 6 "UGC 中心" —— 外部 UGC 信号 + 内部 UGC 资产 + V2 演进
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown(f"""
    <div style="font-size:12px;color:{TERTIARY_TEXT};padding:2px 0 14px;">
        基于多平台 UGC 内容数据，AI 自动解析用户心智与行业趋势
    </div>""", unsafe_allow_html=True)

    try:
        _ue = load_ugc_ext(str(PROJECT_ROOT / "ugc_external.csv"))
        _ui = load_ugc_int(str(PROJECT_ROOT / "ugc_internal.json"))
    except FileNotFoundError:
        st.warning("⚠️ 请先运行 `python3 generate_ugc_data.py` 生成 UGC 数据文件")
        st.stop()

    # ── Section A：外部 UGC 信号 · 行业大盘 ─────────────────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div class="sh">
            <span class="stt">外部 UGC 信号 · 行业大盘</span>
            <span class="ss">综合多平台 UGC 数据 · AI 自动识别趋势 · 周更</span>
            <span class="updt">数据更新于本周一</span>
        </div>""", unsafe_allow_html=True)

        # 计算 Top 4 热度变化款式
        _ud   = _ue["日期"].max()
        _ur30 = (_ue[_ue["日期"] >= _ud - timedelta(days=29)]
                 .groupby("款式名").agg(近30天笔记=("笔记数","sum"), 近30天互动=("互动量","sum")))
        _up30 = (_ue[(_ue["日期"] >= _ud - timedelta(days=59)) &
                     (_ue["日期"] <  _ud - timedelta(days=29))]
                 .groupby("款式名").agg(前30天笔记=("笔记数","sum")))
        _utrd = _ur30.join(_up30, how="left")
        _utrd["涨跌率"] = ((_utrd["近30天笔记"] - _utrd["前30天笔记"])
                          / _utrd["前30天笔记"] * 100).round(1)
        _top4 = _utrd.sort_values("涨跌率", ascending=False).head(4)

        def _udesc(chg):
            if chg > 40: return "社交平台笔记增长显著，用户种草意愿强，是当前高热款式。"
            elif chg > 15: return "稳步上升，热度走高，素人晒图增多，建议适时跟款。"
            elif chg > 0: return "小幅正增长，关注度持续积累，可纳入备选跟款范围。"
            elif chg > -15: return "热度小幅回落，处于正常波动区间，暂不建议主推。"
            else: return "热度回落明显，进入衰退期，建议下调主推优先级。"

        def _utags(chg):
            if chg > 40: return ["高热度", "高传播性"]
            elif chg > 15: return ["上升趋势", "值得关注"]
            elif chg > 0: return ["稳健增长", "持续积累"]
            elif chg > -15: return ["轻微回落", "观望期"]
            else: return ["衰退期", "建议降权"]

        _uc1, _uc2 = st.columns(2, gap="small")
        _uc3, _uc4 = st.columns(2, gap="small")
        for _ucol, (_sty_u, _row_u) in zip([_uc1, _uc2, _uc3, _uc4], _top4.iterrows()):
            _cu    = _row_u["涨跌率"]
            _upc   = "#4D6B5F" if _cu > 0 else "#8E5A4D"
            _ucstr = f"{'↑' if _cu > 0 else '↓'} {abs(_cu):.0f}%"
            _uth   = "".join(f'<span class="ttg">{g}</span>' for g in _utags(_cu))
            _notes = f"{int(_row_u['近30天笔记']):,}"
            _inter = f"{int(_row_u['近30天互动']):,}"
            with _ucol:
                st.markdown(f"""
                <div class="tc">
                    <div class="tch">
                        <span class="tnm">{_sty_u}</span>
                        <span style="color:{_upc};font-size:11px;">热度 {_ucstr}</span>
                    </div>
                    <div class="tds">{_udesc(_cu)}</div>
                    <div style="font-size:10px;color:{TERTIARY_TEXT};margin-bottom:4px;">
                        近30天笔记 {_notes} 篇 · 互动 {_inter}
                    </div>
                    <div class="ttr">{_uth}</div>
                </div>""", unsafe_allow_html=True)
                _upmt = (
                    f"以下是『{_sty_u}』在多平台的 UGC 热度数据，请分析趋势并给出跟款建议。\n\n"
                    f"【外部 UGC 信号（多平台汇总）】\n"
                    f"- 近30天笔记量：{_notes} 篇\n"
                    f"- 近30天互动量：{_inter} 次\n"
                    f"- 热度变化：{_ucstr}（vs 前30天）\n\n"
                    + (f"【本店内部经营数据】\n"
                       f"- 近7天曝光日均：{int(_ds[_sty_u]['exp7_avg']):,}\n"
                       f"- 近7天环比：{_ds[_sty_u]['wow7']*100:+.1f}%\n"
                       f"- 近30天CVR：{_ds[_sty_u]['cvr30']*100:.2f}%\n"
                       if _sty_u in _ds else "【注：本店暂无该款式经营数据】\n") +
                    "\n请按八段式输出分析：\n"
                    "1. 外部热度和内部数据是否一致？\n"
                    "2. 这个款式当前的机会或风险？\n"
                    "3. 具体的跟款/运营动作建议？"
                )
                if st.button("让甲心助手解读 →", key=f"ugc_ext_{_sty_u}"):
                    trigger_dialog(_upmt, f"UGC 趋势解读：{_sty_u}")

    # ── 改造1：商家内容池（V2）────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div class="sh">
            <span class="stt">📤 商家内容池（V2）</span>
            <span class="ss">上传美甲作品 → AI 自动打标签 → 建立内容资产</span>
        </div>""", unsafe_allow_html=True)

        _col_up, _col_res, _col_stat = st.columns([3, 3.5, 3.5], gap="small")

        with _col_up:
            st.markdown(f'<div style="font-size:12px;font-weight:500;color:{PRIMARY_DARK};margin-bottom:6px;">上传区</div>', unsafe_allow_html=True)
            _up_files = st.file_uploader("上传 1-5 张美甲图", type=["jpg","jpeg","png"],
                                          accept_multiple_files=True, key="nail_uploader",
                                          label_visibility="collapsed")
            if _up_files:
                for _uf0 in _up_files[:5]:
                    st.image(_uf0, width=130, caption=_uf0.name[:18])
                if st.button("🤖 让甲心助手识别并归类", key="btn_analyze_imgs"):
                    with st.spinner("甲心助手正在识别美甲图…"):
                        try:
                            _tags_list = _call_vision_api(_up_files, client)
                            _now_str   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            _new_pool  = []
                            for _i2, (_uf2, _tg) in enumerate(zip(_up_files, _tags_list)):
                                _uf2.seek(0)
                                _sp = str(PROJECT_ROOT / "uploads" / f"{_now_str[:10]}_{_i2}_{_uf2.name}")
                                with open(_sp, "wb") as _sf:
                                    _sf.write(_uf2.read())
                                _new_pool.append({"timestamp": _now_str,
                                                   "filename": _uf2.name,
                                                   "filepath": _sp,
                                                   "analysis": _tg})
                            _save_to_content_pool(_new_pool)
                            st.session_state._vision_results   = _tags_list
                            st.session_state._vision_filenames = [_f.name for _f in _up_files]
                            st.toast(f"✅ 成功识别 {len(_tags_list)} 张，已追加到内容池")
                            st.rerun()
                        except Exception as _ve:
                            st.error(f"识别失败：{str(_ve)[:200]}")

        with _col_res:
            st.markdown(f'<div style="font-size:12px;font-weight:500;color:{PRIMARY_DARK};margin-bottom:6px;">解析结果</div>', unsafe_allow_html=True)
            _vr = st.session_state.get("_vision_results", [])
            if not _vr:
                st.markdown(f'<div style="color:{TERTIARY_TEXT};font-size:11px;padding:16px 0;">上传图片后点击识别按钮</div>', unsafe_allow_html=True)
            else:
                for _vt in _vr:
                    st.markdown(f"""
                    <div style="background:{BG_BASE};border:0.5px solid {BORDER};border-radius:8px;
                                padding:10px;margin-bottom:6px;font-size:11px;color:{SECONDARY_TEXT};">
                        <b style="color:{PRIMARY_DARK};">图片 {_vt.get('图片编号','?')}</b> · {_vt.get('款式类型','')}<br>
                        色系：{_vt.get('主色系','')} · 难度：{_vt.get('工艺难度','')}<br>
                        风格：{' '.join(_vt.get('风格标签',[]))}<br>
                        定价：{_vt.get('推荐定价区间','')}
                    </div>""", unsafe_allow_html=True)

        with _col_stat:
            st.markdown(f'<div style="font-size:12px;font-weight:500;color:{PRIMARY_DARK};margin-bottom:6px;">内容池统计</div>', unsafe_allow_html=True)
            _pool_s = _load_content_pool()
            if not _pool_s:
                st.markdown(f'<div style="color:{TERTIARY_TEXT};font-size:11px;">内容池为空，上传图片后显示</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:20px;font-weight:500;color:{PRIMARY_DARK};">{len(_pool_s)}</div><div style="font-size:11px;color:{TERTIARY_TEXT};margin-bottom:8px;">张图片入池</div>', unsafe_allow_html=True)
                _sc = {}
                for _pe2 in _pool_s:
                    _pt2 = _pe2.get("analysis",{}).get("款式类型","其他")
                    _sc[_pt2] = _sc.get(_pt2,0) + 1
                _fig_cp = go.Figure(go.Bar(x=list(_sc.values()), y=list(_sc.keys()),
                                            orientation="h", marker_color=RED_ACCENT))
                _fig_cp.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                      height=110, margin=dict(l=0,r=0,t=0,b=0),
                                      xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                                      yaxis=dict(tickfont=dict(size=10)))
                st.plotly_chart(_fig_cp, use_container_width=True, config={"displayModeBar": False})

        # DNA 重算按钮
        _dna_pool = _load_content_pool()
        if _dna_pool:
            if st.button("🧬 重算店铺视觉 DNA", key="btn_recalc_dna"):
                with st.spinner("甲心助手正在归纳你的视觉 DNA…"):
                    try:
                        from ai_dna_analyzer import analyze_store_dna as _adna
                        _nd = _adna(_dna_pool, client)
                        if "error" not in _nd:
                            st.toast(f"✅ DNA 已更新：{_nd.get('视觉风格 DNA','')[:28]}…")
                            st.rerun()
                        else:
                            st.error(_nd["error"])
                    except Exception as _de:
                        st.error(f"DNA 分析失败：{str(_de)[:200]}")

    # ── Section B：内部 UGC 资产 · 本店 ────────────────────────────────────
    with st.container(border=True):
        st.markdown("""
        <div class="sh">
            <span class="stt">内部 UGC 资产 · 本店</span>
            <span class="ss">基于本店历史 UGC 内容的 AI 解析。V2 将打通真实 UGC 流入与解析。</span>
        </div>""", unsafe_allow_html=True)

        # (1) 4 个指标卡（数据全部从 ugc_internal.json 动态读取）
        _tot_orders = int(dfl["下单数"].sum())
        _ugc_ord    = _ui["UGC引流订单"]
        _ratio      = round(_ugc_ord / _tot_orders * 100, 1) if _tot_orders else 0

        _bi1, _bi2, _bi3, _bi4 = st.columns(4, gap="small")
        _bi1.markdown(_mc("累计 UGC", str(_ui["总条数"]),
                          f"本月 +{_ui['本月新增']}", "up"), unsafe_allow_html=True)
        _bi2.markdown(_mc("好评率", f"{_ui['好评率']:.0%}",
                          "高于商圈均值 87%" if _ui["好评率"] > 0.87 else "接近商圈均值 87%",
                          "up" if _ui["好评率"] > 0.87 else "flat",
                          "商圈均值 87%"), unsafe_allow_html=True)
        _bi3.markdown(_mc("晒图率", f"{_ui['晒图率']:.0%}",
                          "高于行业均值 24%" if _ui["晒图率"] > 0.24 else "接近行业均值 24%",
                          "up" if _ui["晒图率"] > 0.24 else "flat",
                          "行业均值 24%"), unsafe_allow_html=True)
        _bi4.markdown(_mc("UGC 引流订单", str(_ugc_ord),
                          f"占总订单 {_ratio:.1f}%", "up"), unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # (2) 用户心智标签
        st.markdown(f"""
        <div class="sh" style="margin-bottom:8px;">
            <span class="stt" style="font-size:13px;">用户心智标签</span>
            <span class="ss">AI 从 UGC 池提取的 5 个核心标签</span>
        </div>""", unsafe_allow_html=True)

        # ── Bug 4：心智标签全部可点击，弹 modal 解读 ──────────────────────────
        _tcols = st.columns(5, gap="small")
        for _ti, (_tc, _tag) in enumerate(zip(_tcols, _ui["心智标签"])):
            _pos  = _tag["类型"] == "正面"
            _tbg  = BG_BASE if _pos else "#F5E8E3"
            _tcol_txt = PRIMARY_DARK if _pos else "#8E5A4D"
            with _tc:
                st.markdown(f"""
                <div style="background:{_tbg};border:0.5px solid {BORDER};border-radius:8px;
                            padding:10px 8px;text-align:center;">
                    <div style="font-size:12px;font-weight:500;color:{_tcol_txt};">{_tag['标签']}</div>
                    <div style="font-size:10px;color:{TERTIARY_TEXT};margin-top:4px;">
                        频次 {_tag['频次']} · 权重 {_tag['权重']:.0%}
                    </div>
                </div>""", unsafe_allow_html=True)
                _ds_sum = "\n".join(
                    f"- {s}: 近7天曝光 {int(m['exp7_avg']):,} / 30天CVR {m['cvr30']*100:.2f}%"
                    for s, m in _ds.items()
                )
                _tpmt = (
                    f"甲心助手，用户从 UGC 池中看到本店标签「{_tag['标签']}」"
                    f"（频次 {_tag['频次']} 次，权重 {_tag['权重']:.1%}，情感倾向 {_tag['类型']}）。\n\n"
                    f"本店当前后台数据摘要：\n{_ds_sum}\n\n"
                    "请给商家三类建议：\n"
                    "1. 如何强化这个心智（如果是正面标签）/ 如何改善这个心智（如果是负面标签）\n"
                    "2. 这个标签对应的运营动作\n"
                    "3. 风险提醒"
                )
                if st.button("解读 →", key=f"tag_btn_{_ti}", use_container_width=True):
                    trigger_dialog(_tpmt, f"「{_tag['标签']}」· 深度解读")

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # (3) 差评话题聚类
        st.markdown(f"""
        <div class="sh" style="margin-bottom:8px;">
            <span class="stt" style="font-size:13px;">差评话题聚类（近 30 天）</span>
            <span class="ss">AI 自动从负评中归纳的集中话题</span>
        </div>""", unsafe_allow_html=True)

        for _ci, _cp in enumerate(_ui["差评话题"]):
            _cps = _cp.get("关联款式", "全店")
            _cpmt = (
                f"甲心助手，请基于以下用户差评信号给出运营建议。\n\n"
                f"话题：{_cp['话题']}\n"
                f"提及次数：{_cp['提及次数']} 次\n"
                f"占差评比：{_cp['占差评比']:.0%}\n"
                f"样本评论：\"{_cp['样本']}\"\n"
                + (f"\n款式当前后台数据：\n"
                   f"- 近7天曝光日均：{int(_ds[_cps]['exp7_avg']):,}\n"
                   f"- 近30天CVR：{_ds[_cps]['cvr30']*100:.2f}%\n"
                   f"- 近30天总下单：{_ds[_cps]['orders30']} 单\n"
                   if _cps in _ds else "") +
                "\n请按八段式输出，重点回答：\n"
                "1. 这是产品问题、服务问题、还是预期管理问题？\n"
                "2. 不解决会导致什么后果？\n"
                "3. 优先级和成本？"
            )
            _cc1, _cc2 = st.columns([6, 1])
            with _cc1:
                st.markdown(f"""
                <div style="background:{BG_BASE};border:0.5px solid {BORDER};border-radius:8px;
                            padding:12px 14px;margin-bottom:6px;">
                    <div style="font-size:13px;font-weight:600;color:{PRIMARY_DARK};margin-bottom:3px;">
                        {_cp['话题']}
                    </div>
                    <div style="font-size:11px;color:{TERTIARY_TEXT};margin-bottom:6px;">
                        提及 {_cp['提及次数']} 次 · 占差评 {_cp['占差评比']:.0%} · 关联款式：{_cps}
                    </div>
                    <div style="font-size:11px;color:{SECONDARY_TEXT};font-style:italic;">
                        "{_cp['样本']}"
                    </div>
                </div>""", unsafe_allow_html=True)
            with _cc2:
                st.write("")
                if st.button("让甲心\n解读 →", key=f"cp_{_ci}"):
                    trigger_dialog(_cpmt, f"差评解读：{_cp['话题']}")

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # (4) 款式 UGC 表现表格
        st.markdown(f"""
        <div class="sh" style="margin-bottom:8px;">
            <span class="stt" style="font-size:13px;">款式 UGC 表现</span>
        </div>""", unsafe_allow_html=True)
        _ugc_rows = [
            {"款式": sty, "本店UGC数": u["本店UGC数"],
             "好评率": f"{u['好评率']:.0%}",
             "核心好评点": u["核心好评"], "核心差评点": u["核心差评"]}
            for sty, u in _ui["款式UGC"].items()
        ]
        st.dataframe(pd.DataFrame(_ugc_rows), use_container_width=True, hide_index=True)

    # ── 改造3：店铺视觉 DNA 展示 ────────────────────────────────────────────────
    _dna_d = None
    try:
        with open(PROJECT_ROOT / "store_dna.json", encoding="utf-8") as _ff:
            _dna_d = json.load(_ff)
    except FileNotFoundError:
        pass

    if _dna_d and "error" not in _dna_d:
        with st.container(border=True):
            st.markdown(f"""
            <div class="sh">
                <span class="stt">🧬 你的店铺视觉 DNA</span>
                <span class="ss">基于 {_dna_d.get('_sample_count',0)} 张作品自动归纳 ·
                      最后更新 {_dna_d.get('_updated_at','')}</span>
            </div>
            <div style="font-size:20px;font-style:italic;color:{SECONDARY_TEXT};
                        border-left:3px solid {BLUE_ACCENT};padding:10px 16px;margin:4px 0 16px;
                        line-height:1.65;">
                "{_dna_d.get('视觉风格 DNA','')}"
            </div>""", unsafe_allow_html=True)

            _di = [("核心款式定位", _dna_d.get("核心款式定位","")),
                   ("色系倾向",     _dna_d.get("色系倾向","")),
                   ("工艺定位",     _dna_d.get("工艺定位","")),
                   ("目标客群画像", _dna_d.get("目标客群画像","")),
                   ("差异化机会",   _dna_d.get("差异化机会","")),
                   ("潜在风险",     _dna_d.get("潜在风险",""))]
            _da, _db, _dc = st.columns(3, gap="small")
            _dd, _de, _df2 = st.columns(3, gap="small")
            for _dcol, (_dlabel, _dval) in zip([_da,_db,_dc,_dd,_de,_df2], _di):
                _risk = "风险" in _dlabel
                with _dcol:
                    st.markdown(f"""
                    <div style="background:{'#F5E8E3' if _risk else BG_BASE};
                                border:0.5px solid {BORDER};border-radius:8px;padding:12px;">
                        <div style="font-size:10px;color:{TERTIARY_TEXT};margin-bottom:4px;">{_dlabel}</div>
                        <div style="font-size:12px;color:{'#8E5A4D' if _risk else SECONDARY_TEXT};line-height:1.6;">{_dval}</div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{BG_BASE};border:0.5px solid {BORDER};border-radius:8px;
                    padding:16px;text-align:center;color:{TERTIARY_TEXT};margin-bottom:12px;">
            🧬 <b>店铺视觉 DNA</b>：在上方商家内容池上传并解析图片后，点击"重算店铺视觉 DNA"即可生成。
        </div>""", unsafe_allow_html=True)

    # ── Section C：V2 演进 ────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"""
        <div class="sh" style="margin-bottom:6px;">
            <span class="stt">V2 演进：从工具到内容生态</span>
        </div>
        <div style="font-size:12px;color:{SECONDARY_TEXT};line-height:1.85;margin-bottom:16px;">
            V2 将打通三大数据源：① 本地生活平台原生评价　② 社交平台种草笔记　③ 商家自建内容相册。<br>
            统一进入 AI 解析管道，产出店铺心智、款式标签、美甲师风格三大资产。<br>
            内容池将与运营 Agent 形成双向飞轮——让 AI 建议从「流量层」深入到「产品层」。
        </div>""", unsafe_allow_html=True)

        # SVG 飞轮图（5节点水平环）
        st.markdown(f"""
        <div style="display:flex;justify-content:center;padding:6px 0 4px;overflow:visible;">
        <svg width="600" height="106" xmlns="http://www.w3.org/2000/svg"
             style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;overflow:visible;">
            <defs>
                <marker id="arw" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
                    <path d="M0 0 L7 3.5 L0 7 Z" fill="{TERTIARY_TEXT}"/>
                </marker>
            </defs>
            <rect x="0"   y="20" width="95" height="32" rx="6"
                  fill="{BG_BASE}" stroke="{BORDER}" stroke-width="0.8"/>
            <text x="47"  y="40" text-anchor="middle" font-size="11" fill="{PRIMARY_DARK}">UGC 数据</text>
            <line x1="97" y1="36" x2="113" y2="36" stroke="{TERTIARY_TEXT}"
                  stroke-width="1" marker-end="url(#arw)"/>
            <rect x="115" y="20" width="95" height="32" rx="6"
                  fill="{BG_BASE}" stroke="{BORDER}" stroke-width="0.8"/>
            <text x="162" y="40" text-anchor="middle" font-size="11" fill="{PRIMARY_DARK}">AI 解析</text>
            <line x1="212" y1="36" x2="228" y2="36" stroke="{TERTIARY_TEXT}"
                  stroke-width="1" marker-end="url(#arw)"/>
            <rect x="230" y="20" width="95" height="32" rx="6"
                  fill="{BG_BASE}" stroke="{BORDER}" stroke-width="0.8"/>
            <text x="277" y="40" text-anchor="middle" font-size="11" fill="{PRIMARY_DARK}">内容池</text>
            <line x1="327" y1="36" x2="343" y2="36" stroke="{TERTIARY_TEXT}"
                  stroke-width="1" marker-end="url(#arw)"/>
            <rect x="345" y="20" width="95" height="32" rx="6"
                  fill="{PRIMARY_DARK}" stroke="{PRIMARY_DARK}" stroke-width="0.8"/>
            <text x="392" y="40" text-anchor="middle" font-size="11" fill="white">甲心助手</text>
            <line x1="442" y1="36" x2="458" y2="36" stroke="{TERTIARY_TEXT}"
                  stroke-width="1" marker-end="url(#arw)"/>
            <rect x="460" y="20" width="95" height="32" rx="6"
                  fill="{BG_BASE}" stroke="{BORDER}" stroke-width="0.8"/>
            <text x="507" y="40" text-anchor="middle" font-size="11" fill="{PRIMARY_DARK}">商家决策</text>
            <path d="M507 52 Q295 100 47 52" fill="none" stroke="{TERTIARY_TEXT}"
                  stroke-width="1" stroke-dasharray="5 3" marker-end="url(#arw)"/>
            <text x="277" y="100" text-anchor="middle" font-size="10" fill="{TERTIARY_TEXT}">新 UGC</text>
        </svg>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size:11px;color:{TERTIARY_TEXT};text-align:center;margin-top:6px;">
            预计 V2.0 上线时间：2026 Q3
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌Dialog 触发（必须在页面末尾，确保 dialog 渲染在最后）
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.dialog_prompt:
    show_analysis_dialog()
