
import json
from py2neo import Graph
from tqdm import tqdm

# 安全转换为字符串，避免 NoneType 错误
def safe_str(value):
    return str(value) if value is not None else ""

# 从 Neo4j 获取三级结构的知识图谱数据
def get_graph_data_from_neo4j():
    # 连接到 Neo4j 数据库
    graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

    # 查询课程、章节和知识点的三级结构
    query = """
    MATCH (course:课程)-[:包含知识点]->(kp:知识点)
    OPTIONAL MATCH (kp)-[:解释为]->(concept:知识点定义)
    OPTIONAL MATCH (kp)-[:属于章节]->(unit:章节)
    OPTIONAL MATCH (course)-[:对应课程编号]->(course_id:课程编号)
    RETURN 
        course.名称 AS course, 
        unit.名称 AS chapter, 
        kp.名称 AS knowledge,
        concept.内容 AS concept,
        course_id.编号 AS course_id
    """

    try:
        results = graph.run(query)
    except Exception as e:
        print(f"Error: {str(e)}")
        return {}

    nodes = []
    links = []
    node_mapping = {}
    node_id_counter = 0
    data = results.data()

    for result in tqdm(data):
        course = safe_str(result["course"])
        chapter = safe_str(result["chapter"])
        knowledge = safe_str(result["knowledge"])
        concept = safe_str(result["concept"])
        course_id = safe_str(result["course_id"])

        # 添加课程节点
        if course not in node_mapping:
            node_mapping[course] = node_id_counter
            nodes.append({
                "id": node_id_counter,
                "name": course,
                "category": 0,
                "draggable": True,
                "value": 100,
                "symbolSize": 150
            })
            node_id_counter += 1

        # 添加课程编号节点
        if course_id not in node_mapping:
            node_mapping[course_id] = node_id_counter
            nodes.append({
                "id": node_id_counter,
                "name": course_id,
                "category": 3,
                "draggable": True,
                "value": 30,
                "symbolSize": 50
            })
            node_id_counter += 1

        # 添加章节节点
        if chapter not in node_mapping:
            node_mapping[chapter] = node_id_counter
            nodes.append({
                "id": node_id_counter,
                "name": chapter,
                "category": 1,
                "draggable": True,
                "value": 60,
                "symbolSize": 100
            })
            node_id_counter += 1

        # 添加知识点节点
        if knowledge not in node_mapping:
            node_mapping[knowledge] = node_id_counter
            nodes.append({
                "id": node_id_counter,
                "name": knowledge,
                "category": 2,
                "draggable": True,
                "value": 30,
                "symbolSize": 70
            })
            node_id_counter += 1

        # 添加链接
        links.append({
            "source": node_mapping[course],
            "target": node_mapping[course_id],
            "name": "对应课程编号"
        })
        links.append({
            "source": node_mapping[course],
            "target": node_mapping[chapter],
            "name": "包含章节"
        })
        links.append({
            "source": node_mapping[chapter],
            "target": node_mapping[knowledge],
            "name": "包含知识点"
        })
        links.append({
            "source": node_mapping[knowledge],
            "target": node_mapping[chapter],
            "name": "属于章节"
        })

    return {
        "nodes": nodes,
        "links": links,
        "categories": [
            {"name": "课程"},
            {"name": "章节"},
            {"name": "知识点"},
            {"name": "课程编号"}
        ]
    }

# 导出为 JSON 文件
def save_graph_to_json(graph_data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    graph_data = get_graph_data_from_neo4j()
    json_path = "../../data/data.json"
    save_graph_to_json(graph_data, json_path)
    print(f"✅ 三级结构的知识图谱数据已保存为 JSON 文件：{json_path}")