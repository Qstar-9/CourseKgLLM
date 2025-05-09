from flask import Blueprint, request, jsonify, Response, stream_with_context
from functools import wraps
from .auth import (
    create_user, verify_user, get_user_by_username,
    create_chat_session, get_chat_sessions, get_session_history,
    get_session_by_id, add_message_to_session, delete_chat_session
)
from .chat import get_chat_response
import logging
import jwt
import json
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

def token_required(f):
    """验证token的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': '缺少认证令牌', 'success': False}), 401
        
        try:
            token = token.split(' ')[1]  # 移除 "Bearer " 前缀
            data = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            current_user = get_user_by_username(data['username'])
            if not current_user:
                return jsonify({'message': '用户不存在', 'success': False}), 401
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '令牌已过期', 'success': False}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的令牌', 'success': False}), 401
        except Exception as e:
            logger.error(f'验证令牌时出错: {str(e)}')
            return jsonify({'message': '服务器错误', 'success': False}), 500
            
    return decorated

@api.route('/register', methods=['POST'])
def register():
    """注册接口"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': '缺少必要参数', 'success': False}), 400
        
    username = data['username']
    password = data['password']
    
    # 验证用户名和密码的格式
    if len(username) < 3 or len(password) < 6:
        return jsonify({'message': '用户名长度至少3个字符，密码长度至少6个字符', 'success': False}), 400
    
    success = create_user(username, password)
    
    if success:
        return jsonify({'message': '注册成功', 'success': True}), 201
    else:
        return jsonify({'message': '注册失败，用户名可能已存在', 'success': False}), 400

@api.route('/login', methods=['POST'])
def login():
    """登录接口"""
    logger.info("收到登录请求")
    data = request.get_json()
    logger.info(f"登录请求数据: {data}")
    
    if not data or 'username' not in data or 'password' not in data:
        logger.warning("登录请求缺少必要参数")
        return jsonify({'message': '缺少必要参数', 'success': False}), 400
        
    username = data['username']
    password = data['password']
    
    user = verify_user(username, password)
    if user:
        # 生成token
        token = jwt.encode(
            {'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
            'your-secret-key',
            algorithm='HS256'
        )
        return jsonify({
            'message': '登录成功',
            'success': True,
            'token': token,
            'username': username
        }), 200
    else:
        return jsonify({'message': '用户名或密码错误', 'success': False}), 401

@api.route('/verify-token', methods=['GET'])
@token_required
def verify(current_user):
    """验证token接口"""
    return jsonify({
        'message': '令牌有效',
        'success': True,
        'username': current_user['username']
    })

@api.route('/chat-sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    """获取聊天会话列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        sessions = get_chat_sessions(current_user['username'], page, page_size)
        return jsonify({
            'success': True,
            'data': sessions
        })
    except Exception as e:
        logger.error(f'获取会话列表时出错: {str(e)}')
        return jsonify({'message': '获取会话列表失败', 'success': False}), 500

@api.route('/chat-sessions', methods=['POST'])
@token_required
def create_session(current_user):
    """创建新的聊天会话"""
    try:
        data = request.get_json()
        title = data.get('title', f'对话 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        session = create_chat_session(current_user['username'], title)
        return jsonify({
            'success': True,
            'data': session
        })
    except Exception as e:
        logger.error(f'创建会话时出错: {str(e)}')
        return jsonify({'message': '创建会话失败', 'success': False}), 500

@api.route('/chat-sessions/<int:session_id>', methods=['GET'])
@token_required
def get_session(current_user, session_id):
    """获取指定会话的历史记录"""
    try:
        session = get_session_by_id(session_id)
        if not session or session['user_id'] != current_user['id']:
            return jsonify({'message': '会话不存在', 'success': False}), 404
            
        messages = get_session_history(session_id)
        return jsonify({
            'success': True,
            'data': {
                'session': session,
                'messages': messages
            }
        })
    except Exception as e:
        logger.error(f'获取会话详情时出错: {str(e)}')
        return jsonify({'message': '获取会话详情失败', 'success': False}), 500

@api.route('/chat-sessions/<int:session_id>', methods=['DELETE'])
@token_required
def delete_session(current_user, session_id):
    """删除聊天会话"""
    try:
        session = get_session_by_id(session_id)
        if not session or session['user_id'] != current_user['id']:
            return jsonify({'message': '会话不存在', 'success': False}), 404
            
        success = delete_chat_session(session_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'message': '删除会话失败', 'success': False}), 500
    except Exception as e:
        logger.error(f'删除会话时出错: {str(e)}')
        return jsonify({'message': '删除会话失败', 'success': False}), 500

@api.route('/chat-sessions/<int:session_id>/messages', methods=['POST'])
@token_required
def add_message(current_user, session_id):
    """保存会话消息"""
    try:
        session = get_session_by_id(session_id)
        if not session or session['user_id'] != current_user['id']:
            return jsonify({'message': '会话不存在', 'success': False}), 404
            
        data = request.get_json()
        question = data.get('question')
        answer = data.get('answer')
        
        if not question or not answer:
            return jsonify({'message': '问题和答案不能为空', 'success': False}), 400
            
        success = add_message_to_session(session_id, question, answer)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'message': '保存消息失败', 'success': False}), 500
    except Exception as e:
        logger.error(f'添加消息时出错: {str(e)}')
        return jsonify({'message': '添加消息失败', 'success': False}), 500

@api.route('/chat', methods=['POST'])
@token_required
def chat(current_user):
    """处理聊天请求"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        history = data.get('history', [])
        session_id = data.get('session_id')
        
        if not prompt:
            return jsonify({'message': '问题不能为空', 'success': False}), 400

        def generate():
            try:
                for response in get_chat_response(prompt, history):
                    yield f"data: {json.dumps(response)}\n\n"
            except Exception as e:
                logger.error(f'生成回答时出错: {str(e)}')
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream'
        )
    except Exception as e:
        logger.error(f'处理聊天请求时出错: {str(e)}')
        return jsonify({'message': '服务器错误', 'success': False}), 500 