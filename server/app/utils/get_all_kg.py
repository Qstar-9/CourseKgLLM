import json
from py2neo import Graph
from tqdm import tqdm

# 安全转换为字符串，避免 NoneType 错误
def safe_str(value):
    return str(value) if value is not None else ""

# 定义节点类别
CATEGORY_MAPPING = {
    "课程": 0,
    "课程编号": 1,
    "章节": 2,
    "知识点": 3,
    "知识点定义": 4,
    "其他": 5
}

# 从 Neo4j 获取完整知识图谱数据
def get_graph_data_from_neo4j():
    # 连接到 Neo4j 数据库
    graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")

    # 查询所有节点和关系，包括属性
    query = """
    MATCH (a)-[r]->(b)
    RETURN labels(a) AS subject_labels, a AS subject_node, type(r) AS predicate, labels(b) AS object_labels, b AS object_node
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
        # 直接获取字典对象
        subject_node = dict(result["subject_node"])
        object_node = dict(result["object_node"])
        predicate = safe_str(result["predicate"])
        subject_labels = result["subject_labels"]
        object_labels = result["object_labels"]

        # 获取类别
        subject_category = CATEGORY_MAPPING.get(subject_labels[0], 5) if subject_labels else 5
        object_category = CATEGORY_MAPPING.get(object_labels[0], 5) if object_labels else 5

        # 添加节点并保存属性信息
        for node_data, category in [(subject_node, subject_category), (object_node, object_category)]:
            node_name = safe_str(node_data.get("名称", node_data.get("name", "未知节点")))
            if node_name not in node_mapping:
                node_mapping[node_name] = node_id_counter
                nodes.append({
                    "id": node_id_counter,
                    "name": node_name,
                    "category": category,
                    "attributes": {k: safe_str(v) for k, v in node_data.items()},
                    "draggable": True,
                    "value": 50,
                    "symbolSize": 100
                })
                node_id_counter += 1

        # 添加链接
        links.append({
            "source": node_mapping[safe_str(subject_node.get("名称", "未知节点"))],
            "target": node_mapping[safe_str(object_node.get("名称", "未知节点"))],
            "name": predicate,
            "sent": 0
        })

    return {
        "nodes": nodes,
        "links": links,
        "categories": [
            {"name": "课程"},
            {"name": "课程编号"},
            {"name": "章节"},
            {"name": "知识点"},
            {"name": "知识点定义"},
            {"name": "其他"}
        ]
    }

# 导出为 JSON 文件
def save_graph_to_json(graph_data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    graph_data = get_graph_data_from_neo4j()
    json_path = "../../data/all_data.json"
    save_graph_to_json(graph_data, json_path)
    print(f"✅ 带有属性信息的知识图谱数据已保存为 JSON 文件：{json_path}")
