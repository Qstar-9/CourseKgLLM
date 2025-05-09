import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import pymysql
from pymysql.cursors import DictCursor
import logging
from dbutils.pooled_db import PooledDB
import bcrypt

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 密钥配置
SECRET_KEY = "your-secret-key-tcm-graph"  # 实际应用中应该使用环境变量
TOKEN_EXPIRE_HOURS = 24

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'kgllm',
    'charset': 'utf8mb4'
}

# 创建数据库连接池
pool = PooledDB(
    creator=pymysql,
    maxconnections=6,
    mincached=2,
    maxcached=5,
    maxshared=3,
    blocking=True,
    maxusage=None,
    setsession=[],
    ping=0,
    **DB_CONFIG
)

def get_db():
    """获取数据库连接"""
    return pool.connection()

def hash_password(password: str) -> str:
    """使用SHA256哈希密码（旧方法）"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(username: str) -> str:
    """创建JWT token"""
    try:
        expiration = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        payload = {
            'username': username,
            'exp': expiration
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        logger.error(f"Token creation failed: {str(e)}")
        raise

def init_db():
    """初始化数据库表"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # 创建会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status TINYINT DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"初始化数据库表时出错: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_user(username, password):
    """创建新用户（使用bcrypt加密）"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False
            
        # 使用bcrypt加密密码
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 创建用户
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed.decode('utf-8'))
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"创建用户时出错: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user(username, password):
    """验证用户登录（支持新旧两种密码格式）"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            return None
            
        # 尝试bcrypt验证（新格式）
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return user
        except Exception:
            pass
            
        # 尝试SHA256验证（旧格式）
        hashed_password = hash_password(password)
        if hashed_password == user['password']:
            # 更新为新格式的密码
            new_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (new_hashed.decode('utf-8'), user['id'])
            )
            conn.commit()
            return user
            
        return None
    except Exception as e:
        logger.error(f"验证用户时出错: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    """根据用户名获取用户信息"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"获取用户信息时出错: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_chat_session(username, title=None):
    """创建新的聊天会话"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取用户ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return None
            
        # 创建会话
        if not title:
            title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        cursor.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s)",
            (user['id'], title)
        )
        session_id = cursor.lastrowid
        conn.commit()
        
        # 返回创建的会话信息
        cursor.execute("""
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = %s
        """, (session_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"创建会话时出错: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_chat_sessions(username, page=1, page_size=10):
    """获取用户的会话列表"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取用户ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return {'total': 0, 'records': []}
            
        # 计算总记录数
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM chat_sessions
            WHERE user_id = %s AND status = 1
        """, (user['id'],))
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT s.id, s.title, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON s.id = m.session_id
            WHERE s.user_id = %s AND s.status = 1
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT %s OFFSET %s
        """, (user['id'], page_size, offset))
        
        records = cursor.fetchall()
        return {'total': total, 'records': records}
    except Exception as e:
        logger.error(f"获取会话列表时出错: {str(e)}")
        return {'total': 0, 'records': []}
    finally:
        cursor.close()
        conn.close()

def get_session_by_id(session_id):
    """获取会话信息"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT s.*, u.username
            FROM chat_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = %s AND s.status = 1
        """, (session_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"获取会话信息时出错: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_session_history(session_id):
    """获取会话的消息历史"""
    try:
        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT question, answer, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取会话历史时出错: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()

def add_message_to_session(session_id, question, answer):
    """添加消息到会话"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 添加消息
        cursor.execute("""
            INSERT INTO chat_messages (session_id, question, answer)
            VALUES (%s, %s, %s)
        """, (session_id, question, answer))
        
        # 更新会话的更新时间
        cursor.execute("""
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (session_id,))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"添加消息时出错: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_chat_session(session_id):
    """删除会话（软删除）"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE chat_sessions
            SET status = 0
            WHERE id = %s
        """, (session_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"删除会话时出错: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

# 初始化数据库
try:
    init_db()
except Exception as e:
    logger.error(f"初始化数据库失败: {str(e)}") 