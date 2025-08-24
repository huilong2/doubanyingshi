import sqlite3
import logging
from pathlib import Path
import os

logger = logging.getLogger("NewDataManager")

class NewDataManager:
    """新数据库管理器 - 管理电影、电视、音乐、读书数据"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        # 永久指向主数据库
        self.db_path = self.data_dir / "accounts.db"
        self._migrate_if_needed()
        self._init_db()

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
    
    def _init_db(self):
        """在主数据库中初始化表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建电影表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS dianying (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dianying_id TEXT NOT NULL UNIQUE,
                mingcheng TEXT NOT NULL,
                niandai TEXT
            )
            ''')
            
            # 创建电视表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS dianshi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dianshi_id TEXT NOT NULL UNIQUE,
                mingcheng TEXT NOT NULL,
                niandai TEXT
            )
            ''')
            
            # 创建音乐表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS yinyue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                yinyue_id TEXT NOT NULL UNIQUE,
                mingcheng TEXT NOT NULL,
                niandai TEXT
            )
            ''')
            
            # 创建读书表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS dushu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dushu_id TEXT NOT NULL UNIQUE,
                mingcheng TEXT NOT NULL,
                niandai TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化数据库表失败: {str(e)}")
    
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
