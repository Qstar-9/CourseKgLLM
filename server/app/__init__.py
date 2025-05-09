# coding=utf-8
from flask import Flask, jsonify
from flask_cors import CORS
from app.utils.chat_llm import start_model
from app.utils.api import api

# 初始化Flask应用
apps = Flask(__name__)
CORS(apps, resources=r'/*')

# 注册蓝图
from app.views import chat, graph
apps.register_blueprint(chat.mod)
apps.register_blueprint(graph.mod)
apps.register_blueprint(api, url_prefix='/api')

# 初始化模型
start_model()

@apps.route('/', methods=["GET"])
def route_index():
    return jsonify({"message": "You Got It!"})

@apps.errorhandler(404)
def not_found_error(e):
    return jsonify({"message": "DEBUG: " + str(e)}), 404

@apps.errorhandler(403)
def forbidden_error(e):
    return jsonify({"message": str(e)}), 403

# 添加全局错误处理
@apps.errorhandler(500)
def internal_error(e):
    return jsonify({"message": "Internal Server Error"}), 500

@apps.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"message": str(e)}), 500 