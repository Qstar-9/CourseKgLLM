import requests
import json

class Ner:
    def __init__(self):
        self.url = "http://202.127.200.34:30025/v1/chat/completions"
        self.headers = {"Content-Type": "application/json"}
        self.model = "qwen2-7B"

    def predict(self, text, etypes=None):
        """
        使用大模型识别句子中的命名实体（支持多类型）
        """
        if etypes is None:
            etypes = []

        etype_str = "、".join(etypes) if etypes else "所有类型"
        prompt = f"""
请从下列句子中识别出所有属于【{etype_str}】的实体。
你只需要输出一个JSON数组，每个元素为一个字符串，不需要解释，不要输出其他格式。

输入: "{text}"
输出格式示例:
["实体1", "实体2"]
        """

        messages = [
            {"role": "system", "content": "你是一个命名实体识别专家"},
            {"role": "user", "content": prompt}
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.9,
            "max_tokens": 512
        }

        try:
            response = requests.post(self.url, json=data, headers=self.headers)
            result = response.json()["choices"][0]["message"]["content"]
            entities = json.loads(result)
            return entities
        except Exception as e:
            print(f"❌ 实体识别失败: {e}")
            return []

    def get_entities(self, text, etypes=None):
        """
        获取指定类型的实体（透传到 LLM prompt 中）
        """
        return self.predict(text, etypes=etypes)


# from app.utils.ner import Ner

# ner = Ner()
# user_input = "在清华大学学习《人工智能原理》和《自然语言处理》课程时，我遇到了很多挑战。"
# entities = ner.get_entities(user_input, etypes=["课程名称", "人物类", "地点类"])

# print(entities)
# 输出: ["人工智能原理", "自然语言处理", "清华大学"]
