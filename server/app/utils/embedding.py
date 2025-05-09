from transformers import AutoTokenizer, AutoModel
import torch
import json
from tqdm import tqdm
from intent import fuzzy_query_by_course_name  # 替换成你真实导入路径
from py2neo import Graph

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 本地加载模型
model_path = "/home/ubuntu/.cache/modelscope/hub/models/BAAI/bge-m3"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModel.from_pretrained(model_path).to(device)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0]  # CLS token
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings[0].cpu().tolist()

def get_all_courses():
    """
    获取所有课程名称列表
    """
    query = """
    MATCH (c:课程)
    RETURN c.名称 AS course_name
    """
    graph = Graph("http://localhost:7474", user="neo4j", password="cz666888*", name="neo4j")
    courses = graph.run(query).data()
    return [c["course_name"] for c in courses]

def process_course(course_name):
    """
    获取课程中的所有知识点并生成向量表示
    """
    data = fuzzy_query_by_course_name(course_name, query_type=0)
    result = []

    for item in data:
        full_text = f"{item['课程']} - {item['知识点']}: {item['内容介绍']}"
        emb = get_embedding(full_text)
        result.append({
            "course": item["课程"],
            "name": item['知识点'],
            "text": full_text,
            "embedding": emb
        })

    return result

def main():
    # 获取所有课程名称
    all_courses = get_all_courses()
    all_embeddings = []

    print(f"📦 处理 {len(all_courses)} 门课程...")

    for course_name in tqdm(all_courses):
        course_embeddings = process_course(course_name)
        all_embeddings.extend(course_embeddings)

    # 保存到 JSON 文件
    output_path = "all_course_embeddings_bge_m3.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_embeddings, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存所有课程的向量数据文件：{output_path}")

if __name__ == "__main__":
    main()
