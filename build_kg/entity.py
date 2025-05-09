import requests
import json
def extract_entity_via_llm(query):
    """
    使用大模型识别问题中提到的课程名称实体
    """
    prompt = f"""
请从下列问题中提取出涉及的课程名称。你只需要输出课程名称，不需要输出解释，不需要额外内容。

输入: "{query}"
输出格式示例:
["数据结构"]
"""
    # 构造消息
    message = [
        {"role": "system", "content": "你是一个课程名称识别专家"},
        {"role": "user", "content": prompt}
    ]

    # API 地址和配置
    url = "http://202.127.200.34:30025/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "qwen2-7B",
        "messages": message,
        "temperature": 0.3,
        "max_tokens": 512
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()["choices"][0]["message"]["content"]
        entities = json.loads(result)
        return entities[0] if entities else None
    except Exception as e:
        print(f"❌ 实体识别失败: {e}")
        return None
