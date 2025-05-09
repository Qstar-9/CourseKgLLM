import os
import py2neo
from tqdm import tqdm
import argparse
import pandas as pd

# 安全处理函数：清理None、去掉非法字符、裁剪过长文本
def safe_str(x, max_len=3000):
    if pd.isna(x) or x is None:
        return ""
    return str(x).replace('"', '').replace("'", '').strip()[:max_len]

# 导入普通实体
def import_entity(client, type, entity):
    def create_node(client, type, name):
        name = safe_str(name)
        order = """CREATE (n:%s {名称: "%s"})""" % (type, name)
        client.run(order)

    print(f'正在导入【{type}】类实体...')
    for en in tqdm(entity):
        create_node(client, type, en)

# 导入课程实体（带属性，并处理异常）
def import_course_data(client, type, entity):
    print(f'正在导入【{type}】类实体（带属性）...')
    for course in tqdm(entity):
        try:
            node = py2neo.Node(
                type,
                名称=safe_str(course.get("名称", "")),
                描述=safe_str(course.get("描述", "")),
                学分=safe_str(course.get("学分", "")),
                总学时=safe_str(course.get("总学时", "")),
                理论学时=safe_str(course.get("理论学时", "")),
                实验学时=safe_str(course.get("实验学时", "")),
                考核方式=safe_str(course.get("考核方式", ""))
            )
            client.create(node)
        except Exception as e:
            print(f"❗ 出错课程数据：{course}")
            print(f"❗ 错误信息：{e}")
            raise e

# 创建所有关系
def create_all_relationship(client, all_relationship):
    def create_relationship(client, type1, name1, relation, type2, name2):
        name1 = safe_str(name1)
        name2 = safe_str(name2)
        order = """MATCH (a:%s {名称: "%s"}), (b:%s {名称: "%s"}) CREATE (a)-[:%s]->(b)""" % (
            type1, name1, type2, name2, relation)
        client.run(order)

    print("正在导入关系数据...")
    for type1, name1, relation, type2, name2 in tqdm(all_relationship):
        try:
            create_relationship(client, type1, name1, relation, type2, name2)
        except Exception as e:
            print(f"❗ 出错关系：({type1})-[:{relation}]->({type2})")
            print(f"❗ 错误信息：{e}")
            raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据课程Excel文件构建课程知识图谱")
    parser.add_argument('--website', type=str, default='http://localhost:7474', help='Neo4j连接地址')
    parser.add_argument('--user', type=str, default='neo4j', help='用户名')
    parser.add_argument('--password', type=str, default='cz666888*', help='密码')
    parser.add_argument('--dbname', type=str, default='neo4j', help='数据库名称')
    parser.add_argument('--file', type=str, default='data/data.xlsx', help='课程表格路径')
    args = parser.parse_args()

    # 连接Neo4j
    client = py2neo.Graph(args.website, user=args.user, password=args.password, name=args.dbname)

    # 清空数据库
    if input('注意: 是否清空Neo4j现有图谱? (y/n): ').strip().lower() == 'y':
        client.run("MATCH (n) DETACH DELETE n")
        print("图谱已清空。")

    # 读取数据
    df = pd.read_excel(args.file)

    # 初始化实体与关系
    all_entity = {
        "课程": [],
        "教材": [],
        "参考书目": [],
        "专业": [],
        "考试方式": [],
    }
    relationship = []

    # 解析每一行数据
    for idx, row in df.iterrows():
        curriculum_name = safe_str(row.get("curriculumName", ""))
        if not curriculum_name:
            continue

        # 课程实体
        all_entity["课程"].append({
            "名称": curriculum_name,
            "描述": safe_str(row.get("curriculumDescription", "")),
            "学分": safe_str(row.get("credit", "")),
            "总学时": safe_str(row.get("period", "")),
            "理论学时": safe_str(row.get("theoryPeriod", "")),
            "实验学时": safe_str(row.get("experimentPeriod", "")),
            "考核方式": safe_str(row.get("examCategory", ""))
        })

        # 教材
        textbooks = safe_str(row.get("basicTextbook", "")).split("\n") if pd.notna(row.get("basicTextbook", "")) else []
        for tb in textbooks:
            tb = tb.strip()
            if tb:
                all_entity["教材"].append(tb)
                relationship.append(("课程", curriculum_name, "使用教材", "教材", tb))

        # 参考书目
        references = safe_str(row.get("bibliography", "")).split("\n") if pd.notna(row.get("bibliography", "")) else []
        for ref in references:
            ref = ref.strip()
            if ref:
                all_entity["参考书目"].append(ref)
                relationship.append(("课程", curriculum_name, "参考资料", "参考书目", ref))

        # 专业
        majors = safe_str(row.get("major", "")).replace("，", ",").split(",") if pd.notna(row.get("major", "")) else []
        for major in majors:
            major = major.strip()
            if major:
                all_entity["专业"].append(major)
                relationship.append(("课程", curriculum_name, "适用专业", "专业", major))

        # 考核方式
        exam_type = safe_str(row.get("examCategory", ""))
        if exam_type:
            all_entity["考试方式"].append(exam_type)
            relationship.append(("课程", curriculum_name, "考核方式", "考试方式", exam_type))

    # 去重
    relationship = list(set(relationship))
    all_entity = {k: list(set(v)) if k != "课程" else v for k, v in all_entity.items()}

    # 保存实体和关系（可选：备份）
    os.makedirs('data/ent_course', exist_ok=True)
    with open("./data/rel_course.txt", 'w', encoding='utf-8') as f:
        for rel in relationship:
            f.write(" ".join(rel) + '\n')

    for k, v in all_entity.items():
        with open(f'data/ent_course/{k}.txt', 'w', encoding='utf8') as f:
            if k != "课程":
                for i, ent in enumerate(v):
                    f.write(safe_str(ent) + ('\n' if i != len(v) - 1 else ''))
            else:
                for i, ent in enumerate(v):
                    name = safe_str(ent.get("名称", "")) if isinstance(ent, dict) else safe_str(ent)
                    f.write(name + ('\n' if i != len(v) - 1 else ''))

    # 导入实体
    for k in all_entity:
        if k != "课程":
            import_entity(client, k, all_entity[k])
        else:
            import_course_data(client, k, all_entity[k])

    # 导入关系
    create_all_relationship(client, relationship)

    print("✅ 课程知识图谱构建完成！")
