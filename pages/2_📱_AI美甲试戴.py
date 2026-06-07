"""
AI 美甲试戴 · V1 真功能页
C 端用户体验：上传/拍照手图 → 选款式 → Claude Vision + FLUX Kontext Pro 生成戴上效果
"""
import io
import os
import json
import base64
import datetime
import requests
import replicate
import streamlit as st
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── 页面配置 ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 美甲试戴 · 甲心助手",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 色值 ────────────────────────────────────────────────────────────────────
PRIMARY_DARK   = "#2C2C2A"
SECONDARY_TEXT = "#5F5E5A"
TERTIARY_TEXT  = "#B4B2A9"
BG_BASE        = "#F5F4EF"
BG_CARD        = "#FFFFFF"
BORDER         = "#E5E3DC"
GREEN_ACCENT   = "#6B8E7F"

# ── 全局样式 ─────────────────────────────────────────────────────────────────
st.markdown(f"""<style>
.stApp {{ background:{BG_BASE} !important; }}
header[data-testid="stHeader"], footer,
.stDecoration, .stToolbar, .stDeployButton {{ display:none !important; }}
.main .block-container {{ max-width:960px; padding:0 24px 48px; margin:0 auto; }}

/* 上传区虚线边框 */
[data-testid="stFileUploadDropzone"] {{
    border: 1px dashed {BORDER} !important;
    border-radius: 8px !important;
}}

/* 摄像头区域 */
[data-testid="stCameraInput"] {{
    border: 1px dashed {BORDER} !important;
    border-radius: 8px !important;
}}

/* 主生成按钮深灰 */
div[data-testid="stButton"] > button[kind="primary"] {{
    background: {PRIMARY_DARK} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
}}

/* 分享按钮茶绿 */
.share-btn > button {{
    background: {GREEN_ACCENT} !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}}
</style>""", unsafe_allow_html=True)

# ── Session State 初始化 ───────────────────────────────────────────────────
for key, default in [
    ("generated_image", None),
    ("hand_image_ref", None),
    ("style_image_ref", None),
    ("generation_history", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def _pil_from_uploaded(uploaded) -> Image.Image:
    """把 st.file_uploader / st.camera_input 的返回值转成 PIL Image。"""
    if uploaded is None:
        return None
    uploaded.seek(0)
    return Image.open(uploaded).convert("RGB")


def generate_tryon_image(hand_image_pil: Image.Image, style_image_pil: Image.Image) -> Image.Image:
    """
    Claude Vision 描述款式 → FLUX Kontext Pro 编辑手图。
    Step A: Claude 把款式图翻译成详细文字描述
    Step B: FLUX Kontext 把描述应用到手图
    """
    import anthropic

    os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN", "")

    # ── Step A: Claude Vision 描述款式图 ──────────────────────────────────────
    buf = io.BytesIO()
    style_image_pil.save(buf, format="PNG")
    style_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    desc_response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": style_b64},
                },
                {
                    "type": "text",
                    "text": (
                        "Analyze this nail design image and produce a precise visual specification "
                        "that will be used to redraw nails on a different hand. "
                        "Output a single dense paragraph (max 120 words) starting with 'Nail specification: '.\n\n"

                        "Describe in this exact order:\n\n"

                        "1. NAIL SHAPE (be very precise):\n"
                        "   - Overall shape: square / squoval / round / oval / almond / stiletto / coffin/ballerina\n"
                        "   - Tip shape: flat / curved / pointed / tapered\n"
                        "   - Side wall: straight / curved\n\n"

                        "2. NAIL LENGTH (critical for try-on accuracy):\n"
                        "   - Length category: extra short (at fingertip) / short (1-2mm beyond) / "
                        "medium (3-5mm beyond) / long (5-10mm beyond) / extra long (10mm+)\n"
                        "   - Whether these are press-on/extension/sculpted nails (artificial length added) "
                        "or natural nails grown out\n\n"

                        "3. PER-FINGER COLOR & DESIGN (preserve multi-color distribution):\n"
                        "   - Thumb: [color, pattern, finish]\n"
                        "   - Index: [color, pattern, finish]\n"
                        "   - Middle: [color, pattern, finish]\n"
                        "   - Ring: [color, pattern, finish]\n"
                        "   - Pinky: [color, pattern, finish]\n"
                        "   If multi-color, explicitly state which finger has which color.\n\n"

                        "4. PATTERNS / ART:\n"
                        "   - Solid color / French tip / ombre / checkered / floral / abstract art / hearts / rhinestones / glitter\n"
                        "   - Location of art on each finger\n\n"

                        "5. FINISH:\n"
                        "   - Glossy / matte / shimmer / metallic / chrome / jelly\n\n"

                        "Output format example:\n"
                        "'Nail specification: Long coffin-shaped extension nails (8mm beyond fingertip), "
                        "tapered straight sidewalls. Thumb: solid glossy black. Index: black-and-pink "
                        "checkered pattern, glossy. Middle: solid black with single pink heart accent. "
                        "Ring: transparent brown jelly. Pinky: pink-and-black checkered, glossy. "
                        "All nails are artificial press-on style.'\n\n"

                        "Be visually precise. The output will be sent to an image editor that needs to "
                        "actually change the nail shape and length, not just paint over existing nails."
                    ),
                },
            ],
        }],
    )
    style_description = desc_response.content[0].text

    # ── Step B: 手图转 data URI ───────────────────────────────────────────────
    buf2 = io.BytesIO()
    hand_image_pil.save(buf2, format="PNG")
    hand_uri = "data:image/png;base64," + base64.b64encode(buf2.getvalue()).decode("utf-8")

    # ── Step C: 拼接 FLUX prompt ──────────────────────────────────────────────
    flux_prompt = (
        f"Replace the nails in the image with this new design: {style_description}\n\n"
        "CRITICAL: Change the actual nail SHAPE and LENGTH to match the specification above. "
        "If the specification says 'long coffin extensions', the output nails must be long "
        "and coffin-shaped, even if the input hand has short natural nails. "
        "This is a virtual try-on showing what the user would look like wearing these exact nails.\n\n"
        "Preserve from the input image: hand identity, skin tone, finger anatomy, "
        "pose, lighting, and background. Replace only the nails (shape, length, color, pattern)."
    )

    # ── Step D: 调 FLUX Kontext Pro ───────────────────────────────────────────
    output = replicate.run(
        "black-forest-labs/flux-kontext-pro",
        input={
            "prompt": flux_prompt,
            "input_image": hand_uri,
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "safety_tolerance": 2,
        },
    )

    # ── Step E: 处理返回（URL / FileOutput / bytes 三种情况）─────────────────
    if isinstance(output, str):
        resp = requests.get(output, timeout=60)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content))
    elif hasattr(output, "read"):
        return Image.open(output)
    else:
        return Image.open(io.BytesIO(bytes(output)))


def share_to_content_pool():
    """把生成图存到 uploads/，调 Claude Vision 打标签，追加到 content_pool.json。"""
    import anthropic

    generated: Image.Image = st.session_state["generated_image"]
    if generated is None:
        st.warning("没有生成结果可分享。")
        return

    # 1. 保存图片
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    uploads_dir = PROJECT_ROOT / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    img_path = uploads_dir / f"tryon_share_{timestamp}.png"
    generated.save(str(img_path))

    # 2. Claude Vision 打标签
    with open(img_path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    vision_resp = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "请分析这张美甲图片，输出 JSON：\n"
                        "{\n"
                        '  "款式类型": "猫眼/法式/手绘/纯色/穿戴甲/果冻甲/其他",\n'
                        '  "主色系": "颜色描述（约 5-10 字）",\n'
                        '  "风格标签": ["从这些中选 2-3 个：简约/华丽/复古/纯欲/可爱/高级/通勤/约会"],\n'
                        '  "工艺难度": "低/中/高",\n'
                        '  "适合人群": "20-25 字描述",\n'
                        '  "推荐定价区间": "整数范围，单位元"\n'
                        "}\n"
                        "只返回 JSON 本体，不要解释。"
                    ),
                },
            ],
        }],
    )

    try:
        tags = json.loads(vision_resp.content[0].text)
    except Exception:
        tags = {
            "款式类型": "其他",
            "主色系": "未识别",
            "风格标签": [],
            "工艺难度": "中",
            "适合人群": "通用",
            "推荐定价区间": "200-300",
        }

    # 3. 追加到 content_pool.json
    pool_path = PROJECT_ROOT / "content_pool.json"
    if pool_path.exists():
        with open(pool_path, "r", encoding="utf-8") as f:
            pool = json.load(f)
    else:
        pool = []

    new_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": img_path.name,
        "filepath": str(img_path.relative_to(PROJECT_ROOT)),
        "来源": "C端用户试戴生成",
        "analysis": tags,
    }
    pool.append(new_entry)

    with open(pool_path, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    # 4. 成功提示
    st.success("✅ 已分享到商家内容池！AI 已自动识别款式标签")
    st.info(
        f"识别结果：{tags.get('款式类型')} / {tags.get('主色系')} / "
        f"风格 {', '.join(tags.get('风格标签', []))}"
    )
    st.page_link(
        "pages/1_💼_运营驾驶舱.py",
        label="→ 去 UGC 中心查看内容池",
        icon="📊",
    )


# ═══════════════════════════════════════════════════════════════════════════
# 页面内容
# ═══════════════════════════════════════════════════════════════════════════

# ── 顶部说明条 ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#F0EDEA; border-radius:6px; padding:8px 16px; margin-bottom:20px;
            font-size:11px; color:#888780; text-align:center;">
    V1 真功能演示 · Claude Vision 描述款式 + FLUX Kontext Pro 编辑 · 单次生成约 15-20 秒
</div>
""", unsafe_allow_html=True)

# ── 品牌区 ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:32px 0 24px; border-bottom:0.5px solid {BORDER}; margin-bottom:32px;">
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
        <span style="font-size:28px; font-weight:700; color:{PRIMARY_DARK};">📱 AI 美甲试戴</span>
        <span style="background:{BG_BASE}; border:0.5px solid {BORDER}; border-radius:20px;
                     padding:3px 10px; font-size:11px; color:{TERTIARY_TEXT};">
            C 端 · V1 真功能演示
        </span>
    </div>
    <p style="font-size:13px; color:{SECONDARY_TEXT}; margin:0; line-height:1.8;">
        上传你的手图 + 选择心仪款式，<br>
        AI 在 15-20 秒内生成你戴上这款美甲的真实效果。<br>
        保留手部姿态、肤色、背景，完整应用款式的甲型与颜色。
    </p>
</div>
""", unsafe_allow_html=True)

# ── 输入区双栏 ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(f"<div style='font-size:14px; font-weight:600; color:{PRIMARY_DARK}; margin-bottom:10px;'>📸 你的手图</div>", unsafe_allow_html=True)

    input_method = st.radio(
        "选择输入方式",
        options=["📸 拍照", "📁 从相册上传"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
        key="input_method",
    )

    if input_method == "📸 拍照":
        hand_input = st.camera_input("拍摄你的手（建议自然光下五指分开）")
    else:
        hand_input = st.file_uploader(
            "从相册选择手图",
            type=["jpg", "jpeg", "png"],
            key="hand_upload",
        )

    st.markdown(f"<div style='font-size:11px; color:#888780; margin-top:6px;'>💡 手机用户推荐拍照，桌面用户推荐上传 · 摄像头需要 HTTPS 环境才能调起</div>", unsafe_allow_html=True)

with col_right:
    st.markdown(f"<div style='font-size:14px; font-weight:600; color:{PRIMARY_DARK}; margin-bottom:10px;'>💅 选择款式</div>", unsafe_allow_html=True)

    style_method = st.radio(
        "款式来源",
        options=["📁 上传款式图", "🎨 从款式库选"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
        key="style_method",
    )

    style_input = None

    if style_method == "📁 上传款式图":
        style_input = st.file_uploader(
            "上传你喜欢的款式图",
            type=["jpg", "jpeg", "png"],
            key="style_upload",
        )
    else:
        STYLE_OPTIONS = ["奶杏色法式", "透明果冻甲", "复古猫眼", "纯欲粉裸", "手绘油画"]
        style_choice = st.selectbox("选择款式", options=STYLE_OPTIONS)
        style_path = PROJECT_ROOT / f"assets/style_{style_choice}.png"
        if style_path.exists():
            style_input = open(style_path, "rb")
            st.image(str(style_path), width=180, caption=style_choice)
        else:
            st.info(f"款式库图待补充：{style_choice}（请上传对应图片到 assets/style_{style_choice}.png）")
            style_input = None

# ── 生成按钮 ─────────────────────────────────────────────────────────────────
st.markdown("---")
col_btn = st.columns([1, 2, 1])
with col_btn[1]:
    generate_clicked = st.button(
        "🪄 生成我的试戴效果",
        use_container_width=True,
        type="primary",
    )

if generate_clicked:
    if hand_input is None or style_input is None:
        st.warning("请先准备好手图和款式图，再点击生成。")
    else:
        with st.spinner("Claude 分析款式 + FLUX 生成中，预计 15-20 秒..."):
            try:
                hand_pil = _pil_from_uploaded(hand_input)
                style_pil = _pil_from_uploaded(style_input)

                result_img = generate_tryon_image(hand_pil, style_pil)

                st.session_state["generated_image"] = result_img
                st.session_state["hand_image_ref"] = hand_pil
                st.session_state["style_image_ref"] = style_pil

                # 追加历史
                st.session_state["generation_history"].append({
                    "image": result_img,
                    "timestamp": datetime.datetime.now().strftime("%m-%d %H:%M"),
                })

                st.rerun()

            except Exception as e:
                st.error(f"生成失败：{str(e)[:300]}")
                st.info("可能原因：API 配额、Token 无效、图片格式问题。请检查 Replicate 余额或稍后重试。")

# ── 生成结果展示 ──────────────────────────────────────────────────────────────
if st.session_state.get("generated_image") is not None:
    st.markdown(f"### ✨ 试戴效果")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**你的手图**")
        st.image(st.session_state["hand_image_ref"], use_container_width=True)
    with c2:
        st.markdown("**选择的款式**")
        st.image(st.session_state["style_image_ref"], use_container_width=True)
    with c3:
        st.markdown("**🪄 AI 生成效果**")
        st.image(st.session_state["generated_image"], use_container_width=True)

    # 操作按钮行
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("🔄 重新生成", use_container_width=True):
            st.session_state["generated_image"] = None
            st.session_state["hand_image_ref"] = None
            st.session_state["style_image_ref"] = None
            st.rerun()

    with col_b:
        if st.button("📤 分享到商家内容池", type="primary", use_container_width=True):
            with st.spinner("正在打标签并写入内容池..."):
                share_to_content_pool()

    with col_c:
        buf = io.BytesIO()
        st.session_state["generated_image"].save(buf, format="PNG")
        st.download_button(
            "⬇️ 下载图片",
            buf.getvalue(),
            file_name="my_nail_tryon.png",
            mime="image/png",
            use_container_width=True,
        )

# ── 历史记录 ──────────────────────────────────────────────────────────────────
if st.session_state.get("generation_history"):
    st.markdown("---")
    st.markdown(f"### 📜 你的试戴历史")

    history = st.session_state["generation_history"]
    cols = st.columns(4)
    for idx, item in enumerate(reversed(history[-8:])):
        with cols[idx % 4]:
            st.image(item["image"], use_container_width=True)
            st.caption(item["timestamp"])
else:
    st.info("还没有生成记录，快试试上传一张手图开始吧～")

# ── V2 路线图 ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="background:{BG_CARD}; border:0.5px solid {BORDER}; border-radius:12px;
            padding:24px; margin-top:8px;">
    <div style="font-size:14px; font-weight:600; color:{PRIMARY_DARK}; margin-bottom:12px;">🚀 V2 演进</div>
    <div style="font-size:13px; color:{SECONDARY_TEXT}; line-height:1.9;">
        <b>当前 V1</b>：用户试戴 → 生成效果 → 分享到内容池<br>
        <b>V2 演进</b>：<br>
        · 试戴效果一键预约同款门店服务<br>
        · 多手型适配（短手指 / 长手指 / 不同肤色推荐方案）<br>
        · AI 试戴推荐："基于你的手型，这些款式可能更适合你"<br>
        · 商家可设置"虚拟试戴优惠"激励真实到店
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.page_link("home.py", label="← 返回首页")
