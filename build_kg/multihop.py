import requests, json, ast
from py2neo import Graph
from openai import OpenAI
from entity import extract_entity_via_llm  # 你已有的实体识别模块

# ------------------ Neo4j 配置 ------------------ #
graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

INTENT_TO_KG_FIELD = {
    "查询课程描述": {"type": "node", "property": "描述"},
    "查询课程学分": {"type": "node", "property": "学分"},
    "查询课程总学时": {"type": "node", "property": "总学时"},
    "查询课程理论学时": {"type": "node", "property": "理论学时"},
    "查询课程实验学时": {"type": "node", "property": "实验学时"},
    "查询课程考核方式": {"type": "node", "property": "考核方式"},
    "查询课程教材": {"type": "relation", "rel": "使用教材", "target": "教材"},
    "查询课程参考书目": {"type": "relation", "rel": "参考资料", "target": "参考书目"},
    "查询课程适用专业": {"type": "relation", "rel": "适用专业", "target": "专业"},
    "查询课程相关课程": {"type": "relation", "rel": "相关课程", "target": "课程"},
    "查询课程教学目标": {"type": "node", "property": "教学目标"},
    "查询课程先修课程": {"type": "relation", "rel": "先修课程", "target": "课程"},
}

# ------------------ 多跳推理函数 ------------------ #
def multi_hop_query_kg(course_name, intent):
    if intent == "查询课程教材":
        cypher = f'''
        MATCH (c1:课程 {{名称: "{course_name}"}})-[:先修课程]->(c2:课程)-[:使用教材]->(b:教材)
        RETURN collect(b.名称) AS result
        '''
        value = graph.evaluate(cypher)
        if value:
            return "（来自先修课程）" + "、".join(value)

    elif intent == "查询课程参考书目":
        cypher = f'''
        MATCH (c1:课程 {{名称: "{course_name}"}})-[:相关课程]->(c2:课程)-[:参考资料]->(b:参考书目)
        RETURN collect(b.名称) AS result
        '''
        value = graph.evaluate(cypher)
        if value:
            return "（来自相关课程）" + "、".join(value)

    return "未找到相关信息（多跳）"

# ------------------ 主图谱查询函数 ------------------ #
def query_kg(course_name, intents):
    results = []
    for intent in intents:
        config = INTENT_TO_KG_FIELD.get(intent)
        if not config:
            results.append((intent, "❗ 未知意图或未映射字段"))
            continue

        if config["type"] == "node":
            cypher = f'''
                MATCH (c:课程 {{名称: "{course_name}"}})
                RETURN c.{config["property"]} AS result
            '''
            value = graph.evaluate(cypher)
            results.append((intent, value if value else "未找到相关信息"))

        elif config["type"] == "relation":
            cypher = f'''
                MATCH (c:课程 {{名称: "{course_name}"}})-[:{config["rel"]}]->(t:{config["target"]})
                RETURN collect(t.名称) AS result
            '''
            value = graph.evaluate(cypher)
            if value:
                results.append((intent, "、".join(value)))
            else:
                fallback = multi_hop_query_kg(course_name, intent)
                results.append((intent, fallback))
    return results

# ------------------ 意图识别调用 ------------------ #
def api_call(query):
    prompt = f"""...（你的提示词内容不变）...问题输入："{query}" """
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": "qwen2-7B",
        "messages": [{"role":"system","content":"你是一个意图识别专家。"},
                     {"role":"user","content":prompt}],
        "temperature": 0.5,
        "max_tokens": 2048
    }
    response = requests.post("http://202.127.200.34:30025/v1/chat/completions", json=data, headers=headers)
    return json.loads(response.text)['choices'][0]['message']['content']

# ------------------ 主程序入口 ------------------ #
if __name__ == '__main__':
    while True:
        query = input("请输入您的问题: ").strip()
        if not query:
            continue

        entity = extract_entity_via_llm(query)
        intent_str = api_call(query)
        try:
            intents = ast.literal_eval(intent_str)
        except Exception as e:
            print("⚠️ 意图识别结果解析失败：", intent_str)
            continue

        print("📌 实体识别结果:", entity)
        print("📌 意图识别结果:", intents)

        results = query_kg(entity, intents)
        for intent, answer in results:
            print(f"🔎 {intent} → {answer}")
