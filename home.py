"""
甲心助手 · 首页
美业商家 AI 智能体平台入口
启动命令：streamlit run home.py
"""
import streamlit as st

st.set_page_config(
    page_title="甲心助手 - 美业商家 AI 智能体",
    page_icon="💅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 全局 CSS ────────────────────────────────────────────────────────────────
st.markdown("""<style>
.stApp { background: #F5F4EF !important; }
header[data-testid="stHeader"], footer,
.stDecoration, .stToolbar, .stDeployButton { display: none !important; }
.main .block-container { max-width: 960px; padding: 0 24px 48px; margin: 0 auto; }

/* 产品卡片 */
.product-card {
    background: #FFFFFF;
    border: 0.5px solid #E5E3DC;
    border-radius: 16px;
    padding: 32px;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.card-tag {
    background: #F5F4EF;
    border: 0.5px solid #E5E3DC;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: #8E8C84;
    display: inline-block;
    margin-bottom: 12px;
}
.card-title {
    font-size: 22px;
    font-weight: 600;
    color: #2C2C2A;
    margin: 4px 0 6px;
}
.card-subtitle {
    font-size: 13px;
    color: #8E8C84;
    margin-bottom: 20px;
}
.card-bullet {
    font-size: 13px;
    color: #5F5E5A;
    line-height: 1.8;
    margin-bottom: 4px;
}

/* 架构图区域 */
.arch-box {
    background: #FFFFFF;
    border: 0.5px solid #E5E3DC;
    border-radius: 12px;
    padding: 24px 32px;
    margin-top: 24px;
}
.arch-row {
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    margin: 8px 0;
}
.arch-node {
    background: #F5F4EF;
    border: 0.5px solid #E5E3DC;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    color: #2C2C2A;
    text-align: center;
}
.arch-arrow { font-size: 14px; color: #B4B2A9; }

/* page_link 按钮样式 */
[data-testid="stPageLink"] a {
    background: #2C2C2A !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-size: 13px !important;
    text-decoration: none !important;
    display: inline-block !important;
    margin-top: 16px !important;
}
[data-testid="stPageLink"] a:hover {
    background: #444442 !important;
}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌顶部品牌区（居中）
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center; padding: 56px 0 36px;">
    <div style="display:inline-flex; align-items:center; justify-content:center;
                width:56px; height:56px; background:#4A4A47; border-radius:12px;
                color:white; font-size:24px; font-weight:700; margin-bottom:16px;">
        甲
    </div>
    <h1 style="font-size:36px; font-weight:700; color:#2C2C2A; margin:0 0 8px;">
        甲心助手
    </h1>
    <p style="font-size:16px; color:#888780; margin:0;">
        美业商家 AI 智能体 · 双引擎产品
    </p>
</div>
""", unsafe_allow_html=True)

# ── 产品介绍 ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="max-width:640px; margin:0 auto 40px; text-align:center;
            font-size:14px; color:#5F5E5A; line-height:1.85;">
    甲心助手是面向美业商家与用户的 AI 智能体平台。<br>
    B 端运营驾驶舱基于自动巡检 + 趋势分析 + UGC 反哺，<br>
    帮商家把「凭直觉运营」升级为「数据 + 内容双驱动决策」；<br>
    C 端 AI 试戴让用户「看见戴上的真实效果」，<br>
    消除「图片不等于上手」的决策不确定性。
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌两个产品卡片
# ══════════════════════════════════════════════════════════════════════════════
col_l, col_r = st.columns(2, gap="medium")

# ── 左卡片：运营驾驶舱 ──────────────────────────────────────────────────────
with col_l:
    st.markdown("""
    <div class="product-card">
        <div>
            <span class="card-tag">V1 · 已上线</span>
        </div>
        <div style="font-size:32px; margin-bottom:6px;">💼</div>
        <div class="card-title">运营驾驶舱</div>
        <div class="card-subtitle">B 端 · 商家 AI 运营顾问</div>
        <div class="card-bullet">· 自动巡检异常款式，AI 主动预警</div>
        <div class="card-bullet">· 行业趋势 + 商圈大盘对比</div>
        <div class="card-bullet">· UGC 内容池 → 视觉 DNA → 反哺决策</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_💼_运营驾驶舱.py", label="进入驾驶舱 →")

# ── 右卡片：AI 美甲试戴 ─────────────────────────────────────────────────────
with col_r:
    st.markdown("""
    <div class="product-card">
        <div>
            <span class="card-tag">V0 · 验证中</span>
        </div>
        <div style="font-size:32px; margin-bottom:6px;">📱</div>
        <div class="card-title">AI 美甲试戴</div>
        <div class="card-subtitle">C 端 · 用户决策助手</div>
        <div class="card-bullet">· 上传手图 + 选款式</div>
        <div class="card-bullet">· AI 实时生成戴上效果</div>
        <div class="card-bullet">· 消除「图≠上手」的决策不确定性</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_📱_AI美甲试戴.py", label="查看 V0 演示 →")

# ══════════════════════════════════════════════════════════════════════════════
# ▌产品架构示意
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="arch-box">
    <div style="font-size:13px; font-weight:600; color:#2C2C2A; margin-bottom:16px;">
        产品架构
    </div>

    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">

        <!-- B 端流 -->
        <div>
            <div style="font-size:11px; color:#B4B2A9; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em;">
                B 端 · 运营驾驶舱
            </div>
            <div class="arch-row">
                <div class="arch-node">📊 经营数据</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">🤖 Claude AI</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">💡 运营建议</div>
            </div>
            <div class="arch-row">
                <div class="arch-node">📷 商家作品</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">🧬 视觉 DNA</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">🎯 精准策略</div>
            </div>
        </div>

        <!-- C 端流 -->
        <div>
            <div style="font-size:11px; color:#B4B2A9; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.05em;">
                C 端 · AI 美甲试戴
            </div>
            <div class="arch-row">
                <div class="arch-node">🖐 手图上传</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">🎨 Vision AI</div>
                <span class="arch-arrow">→</span>
                <div class="arch-node">✨ 试戴效果</div>
            </div>
            <div class="arch-row" style="justify-content:flex-start; padding-left:8px;">
                <div style="font-size:11px; color:#B4B2A9; line-height:1.7;">
                    用户选款 → 实时渲染 → 降低决策门槛
                </div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ▌技术栈 & 版本信息
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-top:32px; text-align:center; font-size:11px; color:#B4B2A9; line-height:2;">
    <span style="background:#F5F4EF; border:0.5px solid #E5E3DC; border-radius:20px; padding:3px 10px; margin:2px;">
        Streamlit
    </span>
    <span style="background:#F5F4EF; border:0.5px solid #E5E3DC; border-radius:20px; padding:3px 10px; margin:2px;">
        Claude API
    </span>
    <span style="background:#F5F4EF; border:0.5px solid #E5E3DC; border-radius:20px; padding:3px 10px; margin:2px;">
        Plotly
    </span>
    <span style="background:#F5F4EF; border:0.5px solid #E5E3DC; border-radius:20px; padding:3px 10px; margin:2px;">
        Pandas
    </span>
    <br>
    <span style="margin-top:8px; display:inline-block;">
        甲心助手 v1.0 · 2026
    </span>
</div>
""", unsafe_allow_html=True)
