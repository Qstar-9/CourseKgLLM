import os
import sys
sys.path.append('server/app')
import json
import requests
from opencc import OpenCC
from app.utils.image_searcher import ImageSearcher
from app.utils.ner import Ner
from app.utils.graph_utils import convert_graph_to_triples, search_node_item
from app.utils.intent import api_call,query_kg  
import ast
import time
ner = Ner()


API_URL = "http://202.127.200.34:30025/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

def call_llm_api(prompt, history=None):
    """
    调用本地部署的大模型 API，输入 prompt 和历史记录，返回模型回复
    """
    messages = [{"role": "system", "content": "你是一个知识图谱问答助手。"}]
    
    if history:
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
    
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "deepseek-7B",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 2048
    }

    try:
        response = requests.post(API_URL, json=data, headers=HEADERS)
        content = response.json()['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"❌ 调用LLM失败: {e}")
        return "调用模型失败，请稍后再试。"



def stream_predict(user_input, history=None):
    if history is None:
        history = []

    ref = ""
    start_time = time.time()
    timeout = 30  # 设置30秒超时

    # ✅ 实体识别（如课程名）
    entity = ner.get_entities(user_input, etypes=["课程名称"])
    if not entity:
        response = call_llm_api(f"{user_input}")
        yield from yield_response(user_input, response, history)
        return

    print("识别到课程实体:", entity)

    # ✅ 意图识别
    try:
        intent_result = api_call(user_input)
        intent_list = ast.literal_eval(intent_result)
    except Exception as e:
        print("意图解析失败:", e)
        intent_list = []

    print("识别到意图:", intent_list)

    # ✅ 知识图谱查询（含多跳 fallback）
    kg_answers = []
    graph_data = {
        "nodes": [],
        "links": [],
        "categories": []
    }
    related_sentences = set()  # 使用集合去重
    
    for ent in entity:
        if time.time() - start_time > timeout:
            print("⚠️ 查询超时")
            break
            
        ent_answers = query_kg(ent, intent_list, user_input)
        # print("查询到知识图谱答案:", ent_answers)
        
        # 去重处理
        seen_answers = set()
        for intent, result in ent_answers:
            # 处理复杂的结果结构
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        # 构建标准化的答案格式
                        answer_content = []
                        for key, value in item.items():
                            answer_content.append(f"{key}: {value}")
                        answer_text = " | ".join(answer_content)
                        
                        answer_key = f"{ent}:{intent}:{answer_text}"
                        if answer_key not in seen_answers:
                            seen_answers.add(answer_key)
                            kg_answers.append((ent, intent, answer_text))
            else:
                # 处理简单的结果结构
                answer_key = f"{ent}:{intent}:{str(result)}"
                if answer_key not in seen_answers:
                    seen_answers.add(answer_key)
                    kg_answers.append((ent, intent, str(result)))

    # 限制结果数量
    # kg_answers = kg_answers[:10]  # 只保留前10条结果
    # related_sentences = list(related_sentences)[:5]  # 只保留前5条相关描述
    # print(kg_answers)
    # 构建参考文本
    for course, intent, result in kg_answers:
        ref += f"{course}：{intent}：{result}；"

    # 构造 Prompt 作为上下文
    if ref:
        chat_input = f"\n===参考资料===：\n{ref}；\n\n根据上面资料，如实回答下面问题：\n{user_input}"
    else:
        chat_input = user_input
    # 清理旧历史中包含的上下文
    clean_history = []
    for item in history:
        try:
            if isinstance(item, dict) and "content" in item and "response" in item:
                u, r = item["content"], item["response"]
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                u, r = item
            else:
                print(f"⚠️ 跳过非法历史项: {item}")
                continue

            if isinstance(u, str) and "===参考资料===" in u:
                u = u.split("===参考资料===")[0]
            clean_history.append((u, r))
        except Exception as e:
            print(f"⚠️ 跳过异常历史项: {item}，错误信息: {e}")

    # ✅ 发送 LLM 请求
    print("chat_input",chat_input)

    response = call_llm_api(chat_input, clean_history)
    clean_history.append((user_input, response))

    # 构建处理结果
    process_result = {
        "entity_recognition": {
            "entities": entity,
            "status": "success" if entity else "failed"
        },
        "intent_recognition": {
            "intents": intent_list,
            "status": "success" if intent_list else "failed"
        },
        "kg_query": {
            "answers": kg_answers,
            "status": "success" if kg_answers else "failed"
        }
    }

    result = {
        "history": clean_history,
        "updates": {"query": user_input, "response": response},
        "graph": {
            "nodes": graph_data["nodes"],
            "links": graph_data["links"],
            "categories": graph_data["categories"],
            "sents": list(related_sentences)
        },
        "wiki": {
            "title": "课程知识图谱 + 大模型推理",
            "summary": ref or "无参考资料",
            "process_result": process_result
        }
    }

    yield json.dumps(result, ensure_ascii=False).encode('utf8') + b'\n'


def yield_response(user_input, response, history):
    history.append((user_input, response))
    result = {
        "history": history,
        "updates": {"query": user_input, "response": response},
        "graph": {
            "nodes": [],
            "links": [],
            "categories": [],
            "sents": []
        },
        "wiki": {
            "title": "无结果",
            "summary": "实体识别失败",
            "process_result": {
                "entity_recognition": {
                    "entities": [],
                    "status": "failed"
                },
                "intent_recognition": {
                    "intents": [],
                    "status": "failed"
                },
                "kg_query": {
                    "answers": [],
                    "status": "failed"
                }
            }
        }
    }
    yield json.dumps(result, ensure_ascii=False).encode('utf8') + b'\n'

def start_model():
    print("✅ 使用 HTTP 接口调用 Qwen2-7B 模型，无需加载本地模型。")
