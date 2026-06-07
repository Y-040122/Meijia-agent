"""
ai_dna_analyzer.py
调用 Claude API 分析商家内容池，归纳店铺视觉 DNA
可被 nail_agent_app.py 直接 import 调用
"""
import json
import os
import re
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()


def analyze_store_dna(content_pool: list, client=None) -> dict:
    """
    把整个内容池发给 Claude，综合归纳店铺的视觉风格 DNA。

    content_pool : list[dict]，每项含 'analysis' key（来自 content_pool.json）
    client       : anthropic.Anthropic 实例，可复用 app 里的 client 节省初始化开销
    返回         : dict（DNA字段），同时保存到 store_dna.json
    """
    if not content_pool:
        return {"error": "内容池为空，请先上传并解析美甲图片"}

    if client is None:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    analyses = [entry.get("analysis", {}) for entry in content_pool if "analysis" in entry]
    if not analyses:
        return {"error": "内容池中没有有效的图片分析数据"}

    prompt = (
        f"你是美甲行业的品牌咨询师。以下是这家店截至今天的全部作品标签数据（共 {len(analyses)} 张）：\n\n"
        f"{json.dumps(analyses, ensure_ascii=False, indent=2)}\n\n"
        "请综合分析，严格只输出如下 JSON（不要有任何其他文字）：\n"
        "{\n"
        '  "视觉风格 DNA": "一句话概括（约 30 字），描述这家店的核心视觉风格",\n'
        '  "核心款式定位": "1-2 个最突出的款式类型",\n'
        '  "色系倾向": "主导色系倾向",\n'
        '  "工艺定位": "低/中/高 工艺难度的占比与定位描述",\n'
        '  "目标客群画像": "基于风格标签和定价区间推测的目标客群（约 30 字）",\n'
        '  "差异化机会": "这家店相比同行的差异化机会点（约 50 字）",\n'
        '  "潜在风险": "当前内容池暴露的潜在定位风险（约 30 字）"\n'
        "}\n\n"
        "要求：必须基于实际数据归纳，不要编造；数据不足请如实说明。"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw_text = response.content[0].text

    # 提取 JSON（兼容 Claude 在 JSON 前后加文字的情况）
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return {"error": f"无法解析 DNA 输出：{raw_text[:300]}"}

    dna = json.loads(match.group(0))

    # 附加元信息
    dna["_sample_count"] = len(analyses)
    dna["_updated_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 保存（每次重算覆盖）
    with open("store_dna.json", "w", encoding="utf-8") as f:
        json.dump(dna, f, ensure_ascii=False, indent=2)

    return dna


if __name__ == "__main__":
    # 直接运行时：从 content_pool.json 读取数据后分析
    try:
        with open("content_pool.json", encoding="utf-8") as f:
            pool = json.load(f)
        print(f"内容池：{len(pool)} 张图片，开始分析 DNA…")
        result = analyze_store_dna(pool)
        print("\n===  DNA 归纳结果  ===")
        for k, v in result.items():
            if not k.startswith("_"):
                print(f"  {k}：{v}")
    except FileNotFoundError:
        print("未找到 content_pool.json，请先上传图片并解析。")
