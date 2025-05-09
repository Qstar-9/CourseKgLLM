import os
import json
from flask import request, Blueprint, jsonify
from thefuzz import process


mod = Blueprint('graph', __name__, url_prefix='/graph')

##可以调用get_all_kg.py中的函数和convert_triples_graph.py中的函数动态更新展示内容。
@mod.route('/', methods=['GET'])
def graph():
    with open('data/data.json', 'r') as f:
        data = json.load(f)

    return jsonify({
        'data': data,
        'message': 'You Got It!'
    })


@mod.route('/all', methods=['GET'])
def all_graph():
    with open('data/all_data.json', 'r') as f:
        data = json.load(f)

    return jsonify({
        'data': data,
        'message': 'You Got All Data!'
    })


# @mod.route('/search', methods=['GET'])
# def get_triples():
#     # 获取参数
#     user_input = request.args.get('search')
#     result = search_node_item(user_input)

#     return jsonify({
#         'data': result,
#         'message': 'Got it!'
#     })
