import requests
import json
import ollama
import openai
from openai import OpenAI
from app.utils.entity import extract_entity_via_llm
import re
from py2neo import Graph

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
def api_call(query):
    prompt = f"""
阅读下列提示，回答问题（问题在输入的最后）:
当你试图识别用户问题中的查询意图时，你需要仔细分析问题，并在预定义的课程查询类别中逐一进行判断。对于每一个类别，思考用户的问题是否含有与该类别对应的意图。如果符合，就将该类别加入输出列表中。

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
- "查询课程所有章节"
- "查询课程某一章节"
- "查询课程某一知识点"
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
    "查询课程所有章节": {"type": "multi-hop", "subtype": "all_units"},
    "查询课程章节": {"type": "multi-hop", "subtype": "all_units"},
    "查询课程某一章节": {"type": "multi-hop", "subtype": "specific_unit"},
    "查询课程某一知识点": {"type": "multi-hop", "subtype": "specific_kp"},
}

# 连接 Neo4j
graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

def query_specific_unit_kg(course_name, query_text):
    print("输入",course_name,query_text)

    """
    基于课程名+章节编号（如“第一章”）精准查询章节的知识点内容
    """
    # 匹配“第X章”（支持数字或中文）
    match = re.search(r"第([一二三四五六七八九十百千万0-9]+)章", query_text)
    if not match:
        return "未识别出章节名"

    unit_part = match.group(1)

    # 中文数字简易转换
    zh_to_num = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
                 "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}
    if unit_part.isdigit():
        unit_id = unit_part
    else:
        unit_id = "".join([zh_to_num.get(c, c) for c in unit_part])
    print("单章查询",course_name,unit_id)
    # 查询图谱
    cypher = """
    MATCH (c:课程 {名称: $course_name})-[:包含知识点]->(kp:知识点)
          -[:属于章节]->(u:章节 {编号: $unit_id}),
          (kp)-[:解释为]->(concept:知识点定义)
    RETURN u.名称 AS 章节, kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY kp.名称
    """
    result = graph.run(cypher, course_name=course_name, unit_id=unit_id).data()

    if not result:
        return "未找到该章节内容"

    return "\n".join([f"[{r['章节']}] {r['知识点']}: {r['内容介绍']}" for r in result])

# 查询方式一：模糊课程名（正则）
# 查询方式一：模糊课程名（正则）
def fuzzy_query_by_course_name(course_name_pattern, query_type=0):
    print("🟡 原始课程名称模式输入:", course_name_pattern)

    # 正则包装
    if not course_name_pattern.startswith(".*"):
        course_name_pattern = f".*{re.escape(course_name_pattern)}.*"

    print("🟢 正则模式 after escape:", course_name_pattern)

    query = """
    MATCH (c:课程)-[:包含知识点]->(kp:知识点)-[:属于章节]->(u:章节),
          (kp)-[:解释为]->(concept:知识点定义)
    WHERE c.名称 =~ $pattern
    RETURN c.名称 AS 课程, u.名称 AS 章节, u.编号 AS 章节编号,
           kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY u.编号
    """

    result = graph.run(query, pattern=course_name_pattern).data()

    print(f"🔵 查询结果数量: {len(result)}")

    if query_type == 1:
        # 返回知识点列表
        knowledge_points = sorted(set(r["知识点"] for r in result if "知识点" in r))
        print(f"🧠 返回知识点总数: {len(knowledge_points)}")
        return knowledge_points

    elif query_type == 2:
        # 返回章节信息
        chapters = sorted(set((r["章节"], r["章节编号"]) for r in result if "章节" in r))
        print(f"📚 返回章节总数: {len(chapters)}")
        return [{"课程": course_name_pattern, "章节": ch[0], "章节编号": ch[1]} for ch in chapters]

    else:
        # 返回完整信息
        return result




def query_specific_kp_kg(course_name, query_text):
    print("🟢 原始输入：", query_text)
    print("📘 课程名：", course_name)

    # 去掉课程名，保留关键词部分
    cleaned_text = query_text.replace(course_name, "")
    print("🧹 清理后的文本：", cleaned_text)

    # 匹配关键词
    match = re.search(r"(?:中的|关于)?([\u4e00-\u9fa5a-zA-Z0-9]{2,30})", cleaned_text)
    keyword = match.group(1).strip() if match else None

    if not keyword or keyword in course_name:
        return "未识别出有效的知识点关键词"

    # 去除无意义后缀
    keyword = re.sub(r"(是什么|有哪些|的内容|内容|介绍)?$", "", keyword)
    print("🔍 提取的知识点关键词:", keyword)

    # 正则匹配模式（模糊）
    keyword_pattern = f".*{re.escape(keyword)}.*"

    # 图谱查询：正则匹配知识点名称
    cypher = """
    MATCH (c:课程)-[:包含知识点]->(kp:知识点)-[:解释为]->(concept:知识点定义)
    WHERE c.名称 CONTAINS $course_name AND kp.名称 =~ $pattern
    RETURN kp.名称 AS 知识点, concept.内容 AS 内容介绍
    """
    result = graph.run(cypher, course_name=course_name, pattern=keyword_pattern).data()
    print(f"🔎 匹配结果数量: {len(result)}")

    if not result:
        matches = find_kp_by_embedding(query_text, top_k=3)

        if not matches:
            return "未找到相关知识点（向量匹配失败）"
        name, text, score = matches[0]
        return f"{name}:\n{text}\n（相似度: {score:.3f}）"

    return "\n".join([f"{r['知识点']}: {r['内容介绍']}" for r in result])


def find_kp_by_embedding(query_text, top_k=1):
    from transformers import AutoTokenizer, AutoModel
    import torch

    model_path = "/home/ubuntu/.cache/modelscope/hub/models/BAAI/bge-m3"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path).eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    def encode(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0]
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings.cpu().numpy()

    with open("/media/zhjk/rmx/medical/tcm_graph/KGLLM/KnowledgeGraph-based-on-Raw-text-A27-main/server/all_course_embeddings_bge_m3.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    query_vec = encode(query_text)

    sims = []
    for item in all_data:
        vec = np.array(item["embedding"])
        sim = cosine_similarity(query_vec, vec.reshape(1, -1))[0][0]
        sims.append((sim, item))

    sims.sort(reverse=True)
    top_results = sims[:top_k]

    return [(r[1]["name"], r[1]["text"], r[0]) for r in top_results if r[0] > 0.4]

def multi_hop_query_kg(course_name, intent, query_text=None):
    config = INTENT_TO_KG_FIELD[intent]
    subtype = config.get("subtype")

    if subtype == "all_units":
        res=fuzzy_query_by_course_name(course_name,query_type=2)
    
        return res

    elif subtype == "specific_unit":
        # 提取“第几章”或章节名
        res=query_specific_unit_kg(course_name,query_text)
        return res

    elif subtype == "specific_kp":
        res=query_specific_kp_kg(course_name,query_text)
        # matches = find_kp_by_embedding(query_text, top_k=3)

        # if not matches:
        #     return "未找到相关知识点（向量匹配失败）"

        # name, text, score = matches[0]
        # return f"{name}:\n{text}\n（相似度: {score:.3f}）"
        return res

    return "未找到相关信息"

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
        # print(query_specific_unit_kg(entity, query))  # 忽略意图识别，直接测试章节函数

    # course = "大数据计算" 
    # intents = ["查询课程描述", "查询课程教材", "查询课程考核方式"]
        for intent, item in query_kg(entity, result,query):
            print(f"{intent} → {item}")






# # 🚀 主程序（必须放在函数外部）
# if __name__ == '__main__':
#     import ast
#     while True:
#         query = input("请输入您的问题: ")
#         entity = extract_entity_via_llm(query)
#         print("实体识别结果", entity)
#         print("章节查询测试中...")
#         print(query_specific_unit_kg(entity, query))  # 强制测试章节查询
