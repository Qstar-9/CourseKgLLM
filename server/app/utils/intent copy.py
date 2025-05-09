import requests
import json
import ollama
import openai
from openai import OpenAI
from entity import extract_entity_via_llm
import re
def api_call(query):
    prompt = f"""
阅读下列提示，回答问题（问题在输入的最后）:
当你试图识别用户问题中的查询意图时，你需要仔细分析问题，并在12个预定义的课程查询类别中逐一进行判断。对于每一个类别，思考用户的问题是否含有与该类别对应的意图。如果符合，就将该类别加入输出列表中。

**查询类别**
- "查询课程描述"
- "查询课程学分"
- "查询课程总学时"
- "查询课程理论学时"
- "查询课程实验学时"
- "查询课程考核方式"
- "查询课程教材"
- "查询课程参考书目"
- "查询课程适用专业"
- "查询课程相关课程"
- "查询课程教学目标"
- "查询课程先修课程"
- "查询课程章节知识点"
**示例**
输入："这门课讲啥的？"
输出：["查询课程描述"] 

输入："数据结构考什么？"
输出：["查询课程考核方式", "查询课程描述"]  

输入："人工智能这门课推荐哪些教材？"
输出：["查询课程教材"]  

输入："我这个专业可以选这门课吗？"
输出：["查询课程适用专业"]  

输入："数据库课程一共几学时？"
输出：["查询课程总学时"] 

**任务要求**
- 输出必须仅限上述12个类别中选，不得创造新名词。
- 输出意图数量不能超过5个。
- 如果问题涉及课程，一般都会有“查询课程描述”的需求，请优先考虑。
- 仅输出查询到的意图结果列表！

现在请识别下面这个问题的意图：
问题输入："{query}"
输出格式示例：
["查询课程描述", "查询课程教材"] 

"""
    '''
    **示例**
    输入："这门课讲啥的？"
    输出：["查询课程描述"]  # 明显想了解课程内容

    输入："数据结构考什么？"
    输出：["查询课程考核方式", "查询课程描述"]  # 想知道怎么考，还可能想了解课的内容

    输入："人工智能这门课推荐哪些教材？"
    输出：["查询课程教材"]  # 询问教材

    输入："我这个专业可以选这门课吗？"
    输出：["查询课程适用专业"]  # 想知道课程适用于哪些专业

    输入："数据库课程一共几学时？"
    输出：["查询课程总学时"]  # 询问课程时长

    **任务要求**
    - 输出必须仅限上述12个类别中选，不得创造新名词。
    - 输出意图数量不能超过5个。
    - 输出后紧跟注释，用"#"简要说明判断依据。
    - 如果问题涉及课程，一般都会有“查询课程描述”的需求，请优先考虑。

    现在请识别下面这个问题的意图：
    问题输入："{query}"
    输出格式示例：
    ["查询课程描述", "查询课程教材"]  # 该问题想了解课程的内容和使用教材
    '''
    # choice = 'qwen2:latest'
    # try:
    #     rec_result = ollama.generate(model=choice, prompt=prompt)['response']
    #     print(f'意图识别结果:{rec_result}')
    #     return rec_result

    # except Exception as e:
    #     # 捕获任何异常并记录日志
    #     print(f"An error occurred: {e}")
    # 构建初始消息列表，包括系统角色和用户角色
    message = [{"role":"system","content":"你是一个意图识别专家。"}]
    # 将用户输入的prompt添加到消息列表中
    message.append({"role":"user","content":prompt})
    
    # 设置API调用的URL
    url="http://202.127.200.34:30025/v1/chat/completions"
    
    # 设置HTTP请求头，指定内容类型为JSON
    headers = {'Content-Type': 'application/json'}
    
    # 构建请求数据，包括模型名称、消息列表、温度和最大令牌数
    deta={
        "model": "qwen2-7B",
        "messages": message,
        "temperature": 0.5,
        "max_tokens": 2048
    }
    
    # 发送POST请求到API
    response = requests.post(url, json=deta, headers=headers)
    
    # 获取响应文本
    b=response.text
    
    # 将响应文本解析为JSON对象
    d=json.loads(b)
    
    # 返回解析后的JSON对象中第一个选择项的消息内容
    return d['choices'][0]['message']['content']
def multi_hop_query_kg(course_name, intent):
    """执行多跳查询，适用于查询失败后自动尝试路径推理"""
    if intent == "查询课程教材":
        # 二跳：从课程 → 先修课程 → 教材
        cypher = f'''
        MATCH (c1:课程 {{名称: "{course_name}"}})-[:先修课程]->(c2:课程)-[:使用教材]->(b:教材)
        RETURN collect(b.名称) AS result
        '''
        value = graph.evaluate(cypher)
        if value:
            return "（来自先修课程）" + "、".join(value)
    
    elif intent == "查询课程参考书目":
        # 二跳：从课程 → 相关课程 → 参考资料
        cypher = f'''
        MATCH (c1:课程 {{名称: "{course_name}"}})-[:相关课程]->(c2:课程)-[:参考资料]->(b:参考书目)
        RETURN collect(b.名称) AS result
        '''
        value = graph.evaluate(cypher)
        if value:
            return "（来自相关课程）" + "、".join(value)

    return "未找到相关信息（多跳）"

def query_specific_unit_kg(course_name, query_text):
    match = re.search(r"(第[\u4e00-\u9fa5]+章)", query_text)
    if match:
        unit_keyword = match.group(1).replace("章", "").replace("第", "")
        pattern = f".*{re.escape(course_name)}.*"
        unit_match_pattern = f".*{unit_keyword}.*"

        query = """
        MATCH (c:课程)-[:HAS_KNOWLEDGE_POINT]->(kp:知识点)-[:BELONGS_TO_UNIT]->(u:章节),
              (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
        WHERE c.名称 =~ $course_pattern AND u.名称 =~ $unit_pattern
        RETURN u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
        ORDER BY u.名称
        """
        data = graph.run(query, course_pattern=pattern, unit_pattern=unit_match_pattern).data()
        if data:
            return "\n".join([f"[{d['章节']}] {d['知识点']}: {d['内容介绍']}" for d in data])
        return "未找到指定章节的知识点内容。"
    return None
def ollama_call(query):
    choice="deepseek-r1:70b"
    try:
        rec_result = ollama.generate(model=choice, prompt=query)['response']
        print(f'意图识别结果:{rec_result}')
        # return rec_result

    except Exception as e:
        # 捕获任何异常并记录日志
        print(f"An error occurred: {e}")
    #  rec_result = ollama.generate(model=choice, prompt=query)['response']
    #     print(f'意图识别结果:{rec_result}')
def openai_call(query):
    # 设置自定义 API 基础 URL 和 API 密钥
    # 调用 OpenAI API
    try:
        client = OpenAI(
        api_key="sk-ySV9lh42U0XP275mPdXOEYy6ygnva683aBIHvG1Ol7sEk6Nt", 
        base_url="https://api.claudeshop.top/v1",    )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model="gpt-4",
        )
        message=chat_completion.choices[0].message.content
        print(message)
    except Exception as e:
        print(f"An error occurred: {e}")
from py2neo import Graph

# 映射意图到课程知识图谱中的属性或关系字段
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
    "查询课程教学目标": {"type": "node", "property": "教学目标"},  # 可选字段，若有添加
    "查询课程先修课程": {"type": "relation", "rel": "先修课程", "target": "课程"},  # 需提前建图
    "查询课程章节知识点": {"type": "multi-hop"}  # 新增意图：整合章节知识点查询

}

# 连接 Neo4j
graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")
# def query_kg(course_name, intents):
#     results = []
#     for intent in intents:
#         config = INTENT_TO_KG_FIELD.get(intent)
#         if not config:
#             results.append((intent, "❗ 未知意图或未映射字段"))
#             continue

#         if config["type"] == "node":
#             cypher = f'''
#                 MATCH (c:课程 {{名称: "{course_name}"}})
#                 RETURN c.{config["property"]} AS result
#             '''
#             value = graph.evaluate(cypher)
#             results.append((intent, value if value else "未找到相关信息"))
        
#         elif config["type"] == "relation":
#             cypher = f'''
#                 MATCH (c:课程 {{名称: "{course_name}"}})-[:{config["rel"]}]->(t:{config["target"]})
#                 RETURN collect(t.名称) AS result
#             '''
#             value = graph.evaluate(cypher)
#             if value:
#                 results.append((intent, "、".join(value)))
#             else:
#                 # 多跳推理 fallback
#                 print("multi hop")
#                 fallback = multi_hop_query_kg(course_name, intent)
#                 results.append((intent, fallback))
#     return results

def fuzzy_query_by_course_name(course_name_pattern):
    query = """
    MATCH (c:课程)-[:HAS_KNOWLEDGE_POINT]->(kp:知识点)
          -[:BELONGS_TO_UNIT]->(u:章节),
          (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
    WHERE c.名称 =~ $pattern
    RETURN c.名称 AS 课程, u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY u.名称
    """
    return graph.run(query, pattern=course_name_pattern).data()

# 查询方式二：课程编号（精确）
def query_by_course_id(course_id):
    query = """
    MATCH (cid:课程编号 {编号: $course_id})<-[:COURSE_ID_MATCH]-(c:课程)
          -[:HAS_KNOWLEDGE_POINT]->(kp:知识点)
          -[:BELONGS_TO_UNIT]->(u:章节),
          (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
    RETURN c.名称 AS 课程, u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY u.名称
    """
    return graph.run(query, course_id=course_id).data()

# 查询方式三：模糊章节名（正则）
def fuzzy_query_by_unit_name(unit_name_pattern):
    query = """
    MATCH (u:章节)<-[:BELONGS_TO_UNIT]-(kp:知识点)<-[:HAS_KNOWLEDGE_POINT]-(c:课程),
          (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
    WHERE u.名称 =~ $pattern
    RETURN c.名称 AS 课程, u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY c.名称
    """
    return graph.run(query, pattern=unit_name_pattern).data()
# def query_kg(course_name, intents):
#     results = []
#     for intent in intents:
#         config = INTENT_TO_KG_FIELD.get(intent)
#         if not config:
#             results.append((intent, "❗ 未知意图或未映射字段"))
#             continue

#         if config["type"] == "node":
#             cypher = f'''
#                 MATCH (c:课程)
#                 WHERE c.名称 CONTAINS "{course_name}"
#                 RETURN c.{config["property"]} AS result
#             '''
#             value = graph.evaluate(cypher)
#             results.append((intent, value if value else "未找到相关信息"))

#         elif config["type"] == "relation":
#             cypher = f'''
#                 MATCH (c:课程)-[:{config["rel"]}]->(t:{config["target"]})
#                 WHERE c.名称 CONTAINS "{course_name}"
#                 RETURN collect(t.名称) AS result
#             '''
#             value = graph.evaluate(cypher)
#             if value:
#                 results.append((intent, "、".join(value)))
#             else:
#                 results.append((intent, "未找到相关信息"))

#     return results

# === 多跳查询支持章节 ===
def query_specific_unit_kg(course_name, query_text):
    match = re.search(r"(第[\u4e00-\u9fa5]+章)", query_text)
    if not match:
        return None
    unit_ch = match.group(1).replace("第", "").replace("章", "")
    course_pattern = f".*{re.escape(course_name)}.*"
    unit_pattern = f".*{unit_ch}.*"
    cypher = """
    MATCH (c:课程)-[:HAS_KNOWLEDGE_POINT]->(kp:知识点)-[:BELONGS_TO_UNIT]->(u:章节),
          (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
    WHERE c.名称 =~ $course_pattern AND u.名称 =~ $unit_pattern
    RETURN u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
    """
    result = graph.run(cypher, course_pattern=course_pattern, unit_pattern=unit_pattern).data()
    return "\n".join([f"[{r['章节']}] {r['知识点']}: {r['内容介绍']}" for r in result]) if result else "未找到该章节内容"

# def query_kg(course_name, intents,raw_query):
#     results = []
#     for intent in intents:
#         config = INTENT_TO_KG_FIELD.get(intent)
#         if not config:
#             results.append((intent, "❗ 未知意图或未映射字段"))
#             continue

#         if config["type"] == "node":
#             cypher = f'''
#                 MATCH (c:课程)
#                 WHERE c.名称 CONTAINS "{course_name}"
#                 RETURN c.{config["property"]} AS result
#             '''
#             value = graph.evaluate(cypher)
#             results.append((intent, value if value else "未找到相关信息"))

#         elif config["type"] == "relation":
#             # 一跳查询
#             cypher = f'''
#                 MATCH (c:课程)-[:{config["rel"]}]->(t:{config["target"]})
#                 WHERE c.名称 CONTAINS "{course_name}"
#                 RETURN collect(t.名称) AS result
#             '''
#             value = graph.evaluate(cypher)

#             if value:
#                 results.append((intent, "、".join(value)))
#             else:
#                 # ❗ 多跳 fallback 查询
#                 fallback_value = multi_hop_query_kg(course_name, intent,raw_query)
#                 results.append((intent, fallback_value))

#     return results
# 多跳查询
def multi_hop_query_kg(course_name, intent,query_text=""):
    if intent == "查询课程教材":
        query = f"""
        MATCH (c1:课程)-[:先修课程]->(c2:课程)-[:使用教材]->(b:教材)
        WHERE c1.名称 CONTAINS "{course_name}"
        RETURN collect(b.名称) AS result
        """
        value = graph.evaluate(query)
        return "（来自先修课程）" + "、".join(value) if value else "未找到相关信息（多跳）"

    elif intent == "查询课程参考书目":
        query = f"""
        MATCH (c1:课程)-[:相关课程]->(c2:课程)-[:参考资料]->(b:参考书目)
        WHERE c1.名称 CONTAINS "{course_name}"
        RETURN collect(b.名称) AS result
        """
        value = graph.evaluate(query)
        return "（来自相关课程）" + "、".join(value) if value else "未找到相关信息（多跳）"

    elif intent == "查询课程章节知识点":
        spec = query_specific_unit_kg(course_name, query_text)
        if spec: return spec
        cypher = """
        MATCH (c:课程)-[:HAS_KNOWLEDGE_POINT]->(kp:知识点)
              -[:BELONGS_TO_UNIT]->(u:章节),
              (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
        WHERE c.名称 =~ $pattern
        RETURN u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
        """
        pattern = f".*{re.escape(course_name)}.*"
        data = graph.run(cypher, pattern=pattern).data()
        return "\n".join([f"[{d['章节']}] {d['知识点']}: {d['内容介绍']}" for d in data]) if data else "未找到章节内容"


    return "未找到相关信息（多跳）"
# 主函数：执行知识图谱查询
def query_kg(course_name, intents,query):
    results = []
    for intent in intents:
        config = INTENT_TO_KG_FIELD.get(intent)
        if not config:
            results.append((intent, "❗ 未知意图"))
            continue

        if config["type"] == "node":
            cypher = f'''
                MATCH (c:课程)
                WHERE c.名称 CONTAINS "{course_name}"
                RETURN c.{config["property"]} AS result
            '''
            value = graph.evaluate(cypher)
            results.append((intent, value if value else "未找到相关信息"))

        elif config["type"] == "relation":
            cypher = f'''
                MATCH (c:课程)-[:{config["rel"]}]->(t:{config["target"]})
                WHERE c.名称 CONTAINS "{course_name}"
                RETURN collect(t.名称) AS result
            '''
            value = graph.evaluate(cypher)
            if value:
                results.append((intent, "、".join(value)))
            else:
                fallback = multi_hop_query_kg(course_name, intent,query)
                results.append((intent, fallback))

        elif config["type"] == "multi-hop":
            value = multi_hop_query_kg(course_name, intent,query)
            results.append((intent, value))

    return results
import ast
if __name__ == '__main__':
    # openai_call("您好")
    
    while True:
        # pass
        query = input("请输入您的问题: ")
        # result = openai_call(query)
        entity=extract_entity_via_llm(query)
        result=api_call(query)
        result=ast.literal_eval(result)
        print("实体识别结果",entity)
        print(f'意图识别结果:{result}')
    # course = "大数据计算" 
    # intents = ["查询课程描述", "查询课程教材", "查询课程考核方式"]
        for intent, item in query_kg(entity, result,query):
            print(f"{intent} → {item}")