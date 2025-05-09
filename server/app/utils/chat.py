import logging
import json
from typing import Generator, List, Dict, Any
from .chat_llm import stream_predict, start_model

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_chat_response(prompt: str, history: List[Dict[str, str]] = None) -> Generator[Dict[str, Any], None, None]:
    """
    生成聊天响应的生成器函数
    
    Args:
        prompt: 用户输入的问题
        history: 对话历史记录列表
        
    Yields:
        Dict: 包含响应内容的字典
    """
    try:
        logger.info(f"收到聊天请求 - 问题: {prompt}")
        logger.info(f"历史记录: {history}")
        
        # 转换历史记录格式
        chat_history = []
        if history:
            for i in range(0, len(history), 2):
                if i + 1 < len(history):
                    user_msg = history[i]
                    assistant_msg = history[i + 1]
                    if user_msg['role'] == 'user' and assistant_msg['role'] == 'assistant':
                        chat_history.append((user_msg['content'], assistant_msg['content']))
        
        logger.info(f"转换后的历史记录: {chat_history}")
        
        # 使用 stream_predict 生成响应
        for response_bytes in stream_predict(prompt, chat_history):
            try:
                response_str = response_bytes.decode('utf-8').strip()
                logger.info(f"收到响应: {response_str}")
                response_data = json.loads(response_str)
                
                # 更新历史记录
                current_history = []
                for user_msg, assistant_msg in response_data['history']:
                    current_history.append({
                        'role': 'user',
                        'content': user_msg
                    })
                    current_history.append({
                        'role': 'assistant',
                        'content': assistant_msg
                    })
                
                yield {
                    'updates': response_data['updates'],
                    'history': current_history,
                    'image': response_data.get('image', []),
                    'wiki': response_data.get('wiki', {
                        'title': None,
                        'summary': None
                    }),
                    'graph': response_data.get('graph', {
                        'nodes': [],
                        'links': [],
                        'categories': []
                    })
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"解析响应JSON时出错: {str(e)}")
                continue
            
        logger.info("聊天响应生成完成")
        
    except Exception as e:
        logger.error(f"生成聊天响应时出错: {str(e)}")
        yield {
            'error': str(e)
        }

# 启动模型
start_model() 