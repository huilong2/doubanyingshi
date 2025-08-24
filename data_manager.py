import sqlite3
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("DataManager")

class DataManager:
    """统一数据管理器 - 管理数据库和配置文件"""
    
    def __init__(self):
        self.data_dir = self._get_data_dir()
        self.db_path = self._get_db_path()
        self.peizhi_file = self.data_dir / "peizhi.json"
        self._init_data_dir()
        self._init_db()
        self._init_config_file()
    
    def _get_data_dir(self):
        """获取数据目录路径"""
        try:
            from config import config
            return config.data_dir
        except ImportError:
            # 如果配置系统不可用，使用默认路径
            import sys
            if getattr(sys, 'frozen', False):
                # exe打包后的情况
                data_dir = Path(sys.executable).parent / "data"
            else:
                # 开发环境
                data_dir = Path(__file__).parent / "data"
            return data_dir
    
    def _get_db_path(self):
        """获取数据库文件路径"""
        try:
            from config import config
            return config.get_database_path()
        except ImportError:
            return self.data_dir / "accounts.db"
    
    def _init_data_dir(self):
        """初始化数据目录"""
        self.data_dir.mkdir(exist_ok=True)
    
    def _init_config_file(self):
        """初始化配置文件"""
        try:
            if not self.peizhi_file.exists():
                self._save_json(self.peizhi_file, {})
        except Exception as e:
            logger.error(f"初始化配置文件失败: {str(e)}")
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 分组表已删除
        
        # 创建账号表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            ck TEXT,
            nickname TEXT,
            account_id TEXT,
            login_status TEXT,
            homepage TEXT,
            login_time TEXT,
            proxy TEXT,
            running_status TEXT,
            note TEXT,
            gouxuan INTEGER DEFAULT 0
        )
        ''')
        
        # 创建电影表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id TEXT NOT NULL,
            rating TEXT,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建内容表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 默认分组逻辑已删除
        
        # 检查并添加gouxuan字段到accounts表（如果不存在）
        try:
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'gouxuan' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN gouxuan INTEGER DEFAULT 0')
                logger.info("成功添加gouxuan字段到accounts表")
        except Exception as e:
            logger.warning(f"添加gouxuan字段时出现警告: {str(e)}")
        
        conn.commit()
        conn.close()
    
    # ==================== 配置文件管理方法 ====================
    
    def _save_json(self, file_path, data):
        """保存JSON数据到文件"""
        try:
            # 确保数据目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 验证数据格式
            if not isinstance(data, dict):
                raise ValueError("数据必须是字典格式")
            
            # 使用临时文件进行保存
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 如果保存成功，替换原文件
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_file, file_path)
            
            return True
        except Exception as e:
            logger.error(f"保存数据到文件失败: {str(e)}")
            # 清理临时文件
            if temp_file.exists():
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def _load_json(self, file_path):
        """从文件加载JSON数据"""
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if not isinstance(data, dict):
                raise ValueError("数据格式错误")
            
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"从文件加载数据失败: {str(e)}")
            return None
    
    def save_peizhi(self, peizhi_data):
        """保存配置数据到peizhi.json"""
        try:
            # 验证数据格式
            if not isinstance(peizhi_data, dict):
                raise ValueError("配置数据必须是字典格式")
            return self._save_json(self.peizhi_file, peizhi_data)
        except Exception as e:
            logger.error(f"保存配置数据失败: {str(e)}")
            return False
    
    def load_peizhi(self):
        """从peizhi.json加载配置数据"""
        try:
            data = self._load_json(self.peizhi_file)
            return data if data is not None else {}
        except Exception as e:
            logger.error(f"加载配置数据失败: {str(e)}")
            return {}
    
    # ==================== 分组管理方法已删除 ====================
    
    # ==================== 账号管理方法 ====================
    
    def get_accounts(self):
        """获取账号列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY id')
        accounts = cursor.fetchall()
        conn.close()
        return accounts
    
    def add_account(self, account_data):
        """添加账号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 按照表结构顺序插入数据
                cursor.execute('''
                    INSERT INTO accounts (
                        username, password, ck, nickname, account_id,
                        login_status, homepage, login_time, proxy,
                        running_status, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_data['username'],
                    account_data['password'],
                    account_data['ck'],
                    account_data['nickname'],
                    account_data['account_id'],
                    account_data['login_status'],
                    account_data['homepage'],
                    account_data['login_time'],
                    account_data['proxy'],
                    account_data['running_status'],
                    account_data['note']
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def update_account(self, username_or_id, account_data):
        """更新账号信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 更新账号数据
        cursor.execute('''
        UPDATE accounts SET
            username = ?,
            password = ?,
            ck = ?,
            nickname = ?,
            account_id = ?,
            login_status = ?,
            homepage = ?,
            login_time = ?,
            proxy = ?,
            running_status = ?,
            note = ?
        WHERE id = ? OR username = ?
        ''', (
            account_data['username'],
            account_data['password'],
            account_data.get('ck', ''),
            account_data.get('nickname', ''),
            account_data.get('account_id', ''),
            account_data.get('login_status', ''),
            account_data.get('homepage', ''),
            account_data.get('login_time', ''),
            account_data.get('proxy', ''),
            account_data.get('running_status', ''),
            account_data.get('note', ''),
            username_or_id,
            username_or_id
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def update_account_gouxuan(self, account_id, gouxuan_value):
        """更新账号的勾选状态
        
        Args:
            account_id: 账号ID
            gouxuan_value: 勾选状态 (0=未勾选, 1=已勾选)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE accounts SET gouxuan = ? WHERE id = ?
            ''', (gouxuan_value, account_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新账号勾选状态失败: {str(e)}")
            return False
    
    def delete_account(self, account_id):
        """删除账号"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
        return True
    
    # ==================== 电影数据管理方法 ====================
    
    def save_movies(self, movies_data, movie_type):
        """保存电影数据
        
        Args:
            movies_data: 电影数据列表，每个元素为 (movie_id, rating) 元组
            movie_type: 电影类型 ('specific' 或 'random')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 先删除该类型的所有电影
                cursor.execute('DELETE FROM movies WHERE type = ?', (movie_type,))
                # 插入新的电影数据
                cursor.executemany(
                    'INSERT INTO movies (movie_id, rating, type) VALUES (?, ?, ?)',
                    [(movie_id, rating, movie_type) for movie_id, rating in movies_data]
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存电影数据失败: {str(e)}")
            return False
    
    def load_movies(self, movie_type):
        """加载电影数据
        
        Args:
            movie_type: 电影类型 ('specific' 或 'random')
            
        Returns:
            list: 电影数据列表，每个元素为 (movie_id, rating) 元组
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT movie_id, rating FROM movies WHERE type = ? ORDER BY id', (movie_type,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"加载电影数据失败: {str(e)}")
            return []
    
    # ==================== 内容数据管理方法 ====================
    
    def save_contents(self, contents_data, content_type):
        """保存内容数据
        
        Args:
            contents_data: 内容数据列表
            content_type: 内容类型 ('specific' 或 'random')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 先删除该类型的所有内容
                cursor.execute('DELETE FROM contents WHERE type = ?', (content_type,))
                # 插入新的内容数据
                cursor.executemany(
                    'INSERT INTO contents (content, type) VALUES (?, ?)',
                    [(content, content_type) for content in contents_data]
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存内容数据失败: {str(e)}")
            return False
    
    def load_contents(self, content_type):
        """加载内容数据
        
        Args:
            content_type: 内容类型 ('specific' 或 'random')
            
        Returns:
            list: 内容数据列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT content FROM contents WHERE type = ? ORDER BY id', (content_type,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"加载内容数据失败: {str(e)}")
            return []
