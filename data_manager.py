import sqlite3
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger("DataManager")

class DataManager:
    """统一数据管理器 - 管理数据库和配置文件，以及电影、电视、音乐、读书数据"""
    
    def __init__(self, data_dir=None):
        self.data_dir = self._get_data_dir() if data_dir is None else Path(data_dir)
        self.db_path = self._get_db_path()
        self.peizhi_file = self.data_dir / "peizhi.json"
        self._init_data_dir()
        self._init_db()
        self._init_config_file()
        self._migrate_if_needed()
    
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
        
        # 删除 fingerprints 表（如果存在）
        cursor.execute('DROP TABLE IF EXISTS fingerprints')
        
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
            zhiwenshuju TEXT,
            gouxuan INTEGER DEFAULT 0
        )
        '''),
        

        
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
        
        # 创建电影表（新）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dianying (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dianying_id TEXT NOT NULL UNIQUE,
            mingcheng TEXT NOT NULL,
            niandai TEXT
        )
        ''')
        
        # 创建电视表（新）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dianshi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dianshi_id TEXT NOT NULL UNIQUE,
            mingcheng TEXT NOT NULL,
            niandai TEXT
        )
        ''')
        
        # 创建音乐表（新）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS yinyue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            yinyue_id TEXT NOT NULL UNIQUE,
            mingcheng TEXT NOT NULL,
            niandai TEXT
        )
        ''')
        
        # 创建读书表（新）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dushu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dushu_id TEXT NOT NULL UNIQUE,
            mingcheng TEXT NOT NULL,
            niandai TEXT
        )
        ''')
        
        # 默认分组逻辑已删除
        
        # 检查并添加缺失的字段到accounts表
        try:
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'gouxuan' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN gouxuan INTEGER DEFAULT 0')
                logger.info("成功添加gouxuan字段到accounts表")
            if 'zhiwenshuju' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN zhiwenshuju TEXT')
                logger.info("成功添加zhiwenshuju字段到accounts表")
        except Exception as e:
            logger.warning(f"添加字段时出现警告: {str(e)}")
        
        conn.commit()
        conn.close()
    
    def _migrate_if_needed(self):
        """如果旧数据库存在，则执行一次性迁移"""
        source_db_path = self.data_dir / "new_data.db"
        migrated_db_path = self.data_dir / "new_data.db.migrated"

        if not source_db_path.exists():
            return # 无需迁移

        logger.info(f"检测到旧数据库 {source_db_path}，开始迁移数据...")
        dest_db_path = self.db_path

        try:
            source_conn = sqlite3.connect(source_db_path)
            dest_conn = sqlite3.connect(dest_db_path)
            source_cursor = source_conn.cursor()
            dest_cursor = dest_conn.cursor()

            tables_to_migrate = ['dianying', 'dianshi', 'yinyue', 'dushu']

            for table_name in tables_to_migrate:
                logger.debug(f"  -> 正在处理表: {table_name}")
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql_row = source_cursor.fetchone()
                if not create_sql_row:
                    logger.warning(f"    - 表 {table_name} 在源数据库中不存在，跳过。")
                    continue
                
                # 在目标库中创建表（如果不存在）
                dest_cursor.execute(create_sql_row[0])

                source_cursor.execute(f"SELECT * FROM {table_name}")
                all_data = source_cursor.fetchall()
                if not all_data:
                    logger.info(f"    - 表 {table_name} 中没有数据，无需迁移。")
                    continue

                # 使用 INSERT OR IGNORE 避免重复插入
                query = f"INSERT OR IGNORE INTO {table_name} VALUES ({','.join(['?'] * len(all_data[0]))})"
                dest_cursor.executemany(query, all_data)
                dest_conn.commit()
                logger.info(f"    - 成功迁移/合并 {dest_cursor.rowcount} 条记录到表 {table_name}。")

            logger.info("数据迁移成功完成！")

        except sqlite3.Error as e:
            logger.error(f"数据库迁移失败: {e}")
            if 'source_conn' in locals(): source_conn.close()
            if 'dest_conn' in locals(): dest_conn.close()
            return # 迁移失败则中止

        finally:
            if 'source_conn' in locals(): source_conn.close()
            if 'dest_conn' in locals(): dest_conn.close()
        
        # 迁移成功后重命名旧数据库
        try:
            os.rename(source_db_path, migrated_db_path)
            logger.info(f"已将旧数据库重命名为 {migrated_db_path}")
        except OSError as e:
            logger.error(f"重命名旧数据库失败: {e}")
    
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
        
        # 添加调试信息
        logger.debug(f"获取到 {len(accounts)} 个账号")
        for i, account in enumerate(accounts[:3]):  # 只显示前3个账号的调试信息
            logger.debug(f"账号 {i}: ID={account[0]}, 用户名={account[1]}, 勾选状态={account[13] if len(account) > 13 else 'N/A'}")
        
        return accounts
    
    def add_account(self, account_data):
        """添加账号"""
        try:
            # 在方法内部导入以避免循环导入
            from liulanqimokuai.fingerprint_manager import FingerprintGenerator
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 生成指纹数据
                fingerprint_generator = FingerprintGenerator()
                fingerprint_data = fingerprint_generator.generate_random_fingerprint()
                fingerprint_json = json.dumps(fingerprint_data)
                
                # 按照表结构顺序插入数据
                cursor.execute('''
                    INSERT INTO accounts (
                        username, password, ck, nickname, account_id,
                        login_status, homepage, login_time, proxy,
                        running_status, note, zhiwenshuju, gouxuan
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    account_data['note'],
                    fingerprint_json,  # 保存指纹数据
                    0  # 默认不勾选
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
            logger.info(f"开始更新账号勾选状态 - ID: {account_id}, 值: {gouxuan_value}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先检查账号是否存在
            cursor.execute('SELECT id FROM accounts WHERE id = ?', (account_id,))
            result = cursor.fetchone()
            if not result:
                logger.error(f"账号ID {account_id} 不存在于数据库中")
                conn.close()
                return False
            
            cursor.execute('''
            UPDATE accounts SET gouxuan = ? WHERE id = ?
            ''', (gouxuan_value, account_id))
            
            affected_rows = cursor.rowcount
            logger.info(f"更新影响行数: {affected_rows}")
            
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"成功更新账号 {account_id} 勾选状态为 {gouxuan_value}")
                return True
            else:
                logger.error(f"更新账号 {account_id} 勾选状态失败，没有行被影响")
                return False
                
        except Exception as e:
            logger.error(f"更新账号勾选状态失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def get_account_fingerprint(self, account_id):
        """获取账号的指纹数据
        
        Args:
            account_id: 账号ID
            
        Returns:
            str: 指纹数据JSON字符串，如果失败则返回None
        """
        # 检查account_id是否为None
        if account_id is None:
            logger.warning("账号ID为None，无法获取指纹数据")
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT zhiwenshuju FROM accounts WHERE id = ?', (account_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"获取账号指纹数据失败: {str(e)}")
            return None
    
    def update_account_fingerprint(self, account_id, fingerprint_data):
        """更新账号的指纹数据
        
        Args:
            account_id: 账号ID
            fingerprint_data: 指纹数据JSON字符串
            
        Returns:
            bool: 更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE accounts SET zhiwenshuju = ? WHERE id = ?
            ''', (fingerprint_data, account_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新账号指纹数据失败: {str(e)}")
            return False
    
    def delete_account(self, account_id):
        """删除账号，返回是否真的删除了行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    

    

    
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
    
    # ==================== 新增的电影、电视、音乐、读书数据管理方法 ====================
    
    def get_table_counts(self):
        """获取各表的数据量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                counts = {}
                tables = ['dianying', 'dianshi', 'yinyue', 'dushu']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    counts[table] = cursor.fetchone()[0]
                return counts
        except Exception as e:
            logger.error(f"获取表数据量失败: {str(e)}")
            return {}
    
    def get_table_data(self, table_name):
        """获取指定表的所有数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM {table_name}')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取表数据失败: {str(e)}")
            return []
    
    def add_data(self, table_name, data):
        """向指定表添加数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if table_name == 'dianying':
                    cursor.execute('INSERT OR IGNORE INTO dianying (dianying_id, mingcheng, niandai) VALUES (?, ?, ?)', data)
                elif table_name == 'dianshi':
                    cursor.execute('INSERT OR IGNORE INTO dianshi (dianshi_id, mingcheng, niandai) VALUES (?, ?, ?)', data)
                elif table_name == 'yinyue':
                    cursor.execute('INSERT OR IGNORE INTO yinyue (yinyue_id, mingcheng, niandai) VALUES (?, ?, ?)', data)
                elif table_name == 'dushu':
                    cursor.execute('INSERT OR IGNORE INTO dushu (dushu_id, mingcheng, niandai) VALUES (?, ?, ?)', data)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"添加数据失败: {str(e)}")
            return False
    
    def update_data(self, table_name, data, data_id):
        """更新指定表中的数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if table_name == 'dianying':
                    cursor.execute('UPDATE dianying SET dianying_id=?, mingcheng=?, niandai=? WHERE id=?', 
                                 (data[0], data[1], data[2], data_id))
                elif table_name == 'dianshi':
                    cursor.execute('UPDATE dianshi SET dianshi_id=?, mingcheng=?, niandai=? WHERE id=?', 
                                 (data[0], data[1], data[2], data_id))
                elif table_name == 'yinyue':
                    cursor.execute('UPDATE yinyue SET yinyue_id=?, mingcheng=?, niandai=? WHERE id=?', 
                                 (data[0], data[1], data[2], data_id))
                elif table_name == 'dushu':
                    cursor.execute('UPDATE dushu SET dushu_id=?, mingcheng=?, niandai=? WHERE id=?', 
                                 (data[0], data[1], data[2], data_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新数据失败: {str(e)}")
            return False
    
    def delete_data(self, table_name, data_id):
        """删除指定表中的数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'DELETE FROM {table_name} WHERE id=?', (data_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除数据失败: {str(e)}")
            return False
