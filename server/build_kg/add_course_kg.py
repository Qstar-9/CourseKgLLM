import pandas as pd
from py2neo import Graph, Node, Relationship
from tqdm import tqdm
import logging
import csv

# 启用日志记录
logging.basicConfig(level=logging.INFO)

# 清洗函数
def safe_str(x, max_len=3000):
    if pd.isna(x) or x is None:
        return ""
    return str(x).replace('"', '').replace("'", "").strip()[:max_len]
def add_kg():
    # 1. 读取数据
    df = pd.read_excel("/media/zhjk/rmx/medical/tcm_graph/KGLLM/data/course_chapter.xlsx")

    # 2. 连接 Neo4j
    graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

    # 3. 存储三元组
    triples = []

    # 4. 遍历数据构建图谱
    for _, row in tqdm(df.iterrows(), total=len(df)):
        course_name = safe_str(row["curriculum"])
        course_id = str(row["curriculumId"])
        knowledge_point = safe_str(row["knowledgePointName"])
        concept = safe_str(row["knowledgePointConcept"])
        unit = safe_str(row["unit"])
        unit_id = str(row["unitID"])

        # 创建节点
        course_node = Node("课程", 名称=course_name)
        graph.merge(course_node, "课程", "名称")

        course_id_node = Node("课程编号", 编号=course_id)
        graph.merge(course_id_node, "课程编号", "编号")

        kp_node = Node("知识点", 名称=knowledge_point)
        graph.merge(kp_node, "知识点", "名称")

        concept_node = Node("知识点定义", 内容=concept)
        graph.merge(concept_node, "知识点定义", "内容")

        unit_node = Node("章节", 名称=unit, 编号=unit_id)
        graph.merge(unit_node, "章节", "名称")  # 编号作为属性保存

        # 创建关系并添加三元组
        graph.merge(Relationship(course_node, "包含知识点", kp_node))
        triples.append((course_name, "包含知识点", knowledge_point))

        graph.merge(Relationship(kp_node, "解释为", concept_node))
        triples.append((knowledge_point, "解释为", concept))

        graph.merge(Relationship(kp_node, "属于章节", unit_node))
        triples.append((knowledge_point, "属于章节", f"{unit}（编号：{unit_id}）"))

        graph.merge(Relationship(course_node, "对应课程编号", course_id_node))
        triples.append((course_name, "对应课程编号", course_id))

    # 5. 导出三元组到 json
    import json

    # 生成 JSON 格式的三元组
    triple_json = [
        {"subject": s, "predicate": p, "object": o}
        for (s, p, o) in triples
    ]

    # 保存到 JSON 文件
    json_path = "./course_triples.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(triple_json, f, ensure_ascii=False, indent=2)

    print(f"✅ 三元组已保存为 JSON 文件：{json_path}")


# import pandas as pd
# from py2neo import Graph, Node, Relationship
# from tqdm import tqdm
# import logging
# graph = Graph("http://localhost:7474", user="neo4j",password="cz666888*",name="neo4j")

# def get_unit_knowledge_points(course_name, unit_name):
#     query = """
#     MATCH (c:课程 {名称: $course_name})-[:HAS_KNOWLEDGE_POINT]->(kp:知识点)-[:BELONGS_TO_UNIT]->(u:章节 {名称: $unit_name}),
#           (kp)-[:HAS_CONCEPT]->(concept:知识点定义)
#     RETURN kp.名称 AS 知识点, concept.内容 AS 内容介绍
#     """
#     result = graph.run(query, course_name=course_name, unit_name=unit_name).data()
#     return result if result else "没有找到该章节的知识点内容。"

# # 示例使用
# unit_name = "计算与社会+计算机新技术"
# course_name = "大学计算机基础"
# descriptions = get_unit_knowledge_points(course_name, unit_name)

# if isinstance(descriptions, str):
#     print(descriptions)
# else:
#     for item in descriptions:
#         print(f"- 知识点: {item['知识点']}\n  内容介绍: {item['内容介绍']}\n")

# from py2neo import Graph
# import logging

# # 启用日志
# logging.basicConfig(level=logging.INFO)


import re
# 连接 Neo4j
graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

# 查询方式一：模糊课程名（正则）
def fuzzy_query_by_course_name(course_name_pattern):
    import re
    print("🟡 原始课程名称模式输入:", course_name_pattern)

    # 正则包装
    if not course_name_pattern.startswith(".*"):
        course_name_pattern = f".*{re.escape(course_name_pattern)}.*"

    print("🟢 正则模式 after escape:", course_name_pattern)

    query = """
    MATCH (c:课程)-[:包含知识点]->(kp:知识点)
          -[:属于章节]->(u:章节),
          (kp)-[:解释为]->(concept:知识点定义)
    WHERE c.名称 =~ $pattern
    RETURN c.名称 AS 课程, u.名称 AS 章节, u.编号 AS 章节编号,
           kp.名称 AS 知识点, concept.内容 AS 内容介绍
    ORDER BY u.编号
    """

    result = graph.run(query, pattern=course_name_pattern).data()

    print(f"🔵 查询结果数量: {len(result)}")
    if result:
        print("🔍 前3条结果样例:")
        for r in result[:3]:
            print(f"课程: {r['课程']}, 章节: {r['章节']}（编号: {r['章节编号']}）, 知识点: {r['知识点']}")

    return result



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

# 示例调用
if __name__ == "__main__":
    # 模糊匹配课程名（正则表达式，如开头是“大学”的课程）
    # results = fuzzy_query_by_course_name("大学.*")

    # 精确匹配课程编号
    # results = query_by_course_id("502009")

    # 模糊匹配章节名
    results = fuzzy_query_by_course_name("大数据计算")

    for item in results:
        print(f"\n📘 课程: {item['课程']}\n📂 章节: {item['章节']}\n🔹 知识点: {item['知识点']}\n📝 内容介绍: {item['内容介绍']}\n")
