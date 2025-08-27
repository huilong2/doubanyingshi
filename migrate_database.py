# migrate_database.py
import sqlite3
import sys
from pathlib import Path

# 确保可以正确导入项目模块
try:
    from config import DATA_DIR
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from config import DATA_DIR


def migrate_data():
    """将 new_data.db 的数据迁移到 accounts.db"""
    source_db_path = DATA_DIR / "new_data.db"
    dest_db_path = DATA_DIR / "accounts.db"

    if not source_db_path.exists():
        print(f"源数据库 {source_db_path} 不存在，无需迁移.")
        return

    print(f"开始从 {source_db_path} 迁移数据到 {dest_db_path}")

    try:
        source_conn = sqlite3.connect(source_db_path)
        dest_conn = sqlite3.connect(dest_db_path)
        source_cursor = source_conn.cursor()
        dest_cursor = dest_conn.cursor()

        tables_to_migrate = ['dianying', 'dianshi', 'yinyue', 'dushu']

        for table_name in tables_to_migrate:
            print(f"  -> 正在处理表: {table_name}")

            # 1. 从源数据库获取建表语句
            source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_table_sql = source_cursor.fetchone()
            if not create_table_sql:
                print(f"    - 表 {table_name} 在源数据库中不存在，跳过。")
                continue

            # 2. 在目标数据库中创建表 (如果不存在)
            #    在SQL中加入 IF NOT EXISTS 确保安全
            create_sql = create_table_sql[0].replace(f"CREATE TABLE {table_name}", f"CREATE TABLE IF NOT EXISTS {table_name}")
            dest_cursor.execute(create_sql)
            print(f"    - 确保表 {table_name} 在目标数据库中存在。")

            # 3. 从源数据库读取所有数据
            source_cursor.execute(f"SELECT * FROM {table_name}")
            all_data = source_cursor.fetchall()
            if not all_data:
                print(f"    - 表 {table_name} 中没有数据，无需迁移。")
                continue

            # 4. 将数据插入目标数据库
            #    为了避免重复，我们基于ID进行检查
            #    假设第一列是主键ID，第二列是唯一的业务ID (e.g., dianying_id)
            query = f"INSERT OR IGNORE INTO {table_name} VALUES ({','.join(['?'] * len(all_data[0]))})"
            dest_cursor.executemany(query, all_data)
            conn_committed = dest_conn.commit() # commit changes

            print(f"    - 成功迁移 {len(all_data)} 条记录到表 {table_name}。")

        print("\n数据迁移成功完成！")

    except sqlite3.Error as e:
        print(f"数据库操作失败: {e}")
    finally:
        if 'source_conn' in locals():
            source_conn.close()
        if 'dest_conn' in locals():
            dest_conn.close()

if __name__ == "__main__":
    migrate_data()
