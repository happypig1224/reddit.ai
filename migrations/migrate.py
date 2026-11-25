#!/usr/bin/env python3
"""
Reddit Karma Pilot - Database Migration Manager
Compliant with Flyway/Liquibase patterns & db-migration-manager skill guidelines.
"""

import os
import re
import sys
import time
import hashlib
from pathlib import Path
import pymysql

# 兼容 Windows 控制台输出 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 数据库连接默认配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "reddit_karma_pilot")

MIGRATIONS_DIR = Path(__file__).parent
MIGRATION_FILE_PATTERN = re.compile(r"^V(\d+(?:\.\d+)*)__(.+)\.sql$")


def get_connection(include_db=True):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if include_db else None,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


def ensure_database():
    """保证目标数据库存在并采用 utf8mb4 字符集"""
    conn = get_connection(include_db=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
                DEFAULT CHARACTER SET utf8mb4
                DEFAULT COLLATE utf8mb4_unicode_ci;
            """)
        conn.commit()
    finally:
        conn.close()


def ensure_schema_version_table(conn):
    """创建 Flyway 风格的版本管理表"""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `schema_version` (
                `installed_rank` INT NOT NULL AUTO_INCREMENT,
                `version` VARCHAR(50) NOT NULL,
                `description` VARCHAR(200) NOT NULL,
                `type` VARCHAR(20) NOT NULL DEFAULT 'SQL',
                `script` VARCHAR(1000) NOT NULL,
                `checksum` VARCHAR(64) DEFAULT NULL,
                `installed_by` VARCHAR(100) NOT NULL,
                `installed_on` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `execution_time` INT NOT NULL,
                `success` TINYINT(1) NOT NULL,
                PRIMARY KEY (`installed_rank`),
                UNIQUE KEY `uk_version` (`version`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='版本化迁移流水记录表';
        """)
    conn.commit()


def get_applied_migrations(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT version, checksum, success FROM schema_version ORDER BY installed_rank ASC")
        rows = cursor.fetchall()
        return {r["version"]: r for r in rows}


def parse_migration_files():
    files = []
    for file_path in MIGRATIONS_DIR.glob("V*__*.sql"):
        match = MIGRATION_FILE_PATTERN.match(file_path.name)
        if match:
            raw_version = match.group(1)
            desc = match.group(2).replace("_", " ")
            # 格式化版本号用于排序 (例如 1.0.0 -> (1, 0, 0))
            version_tuple = tuple(int(p) for p in raw_version.split("."))
            files.append({
                "raw_version": raw_version,
                "version_tuple": version_tuple,
                "description": desc,
                "file_path": file_path,
                "filename": file_path.name
            })
    files.sort(key=lambda x: x["version_tuple"])
    return files


def split_sql_statements(sql_text):
    """安全拆分 SQL 语句，忽略注释"""
    statements = []
    current = []
    for line in sql_text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("--") or not trimmed:
            continue
        current.append(line)
        if trimmed.endswith(";"):
            statement = "\n".join(current).strip()
            if statement.endswith(";"):
                statement = statement[:-1]
            statements.append(statement)
            current = []
    if current:
        trailing = "\n".join(current).strip()
        if trailing:
            statements.append(trailing)
    return statements


def run_migrations():
    print("=" * 70)
    print("🚀 [db-migration-manager] 正在初始化与应用版本化迁移...")
    print(f"📦 目标数据库: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 70)

    ensure_database()
    conn = get_connection(include_db=True)

    try:
        ensure_schema_version_table(conn)
        applied = get_applied_migrations(conn)
        available = parse_migration_files()

        if not available:
            print("⚠️ 未发现任何版本化迁移文件 (V*__*.sql)")
            return

        migrated_count = 0
        for item in available:
            v = item["raw_version"]
            content = item["file_path"].read_text(encoding="utf-8")
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

            if v in applied:
                record = applied[v]
                if not record["success"]:
                    print(f"❌ 版本 {v} 在历史执行中失败，请人工排查！")
                    sys.exit(1)
                if record["checksum"] and record["checksum"] != checksum:
                    print(f"⚠️ 警告: 已执行的脚本 {item['filename']} 内容发生变动（Checksum 不一致）！")
                else:
                    print(f"⏩ [已跳过] {item['filename']} (版本 {v} 已成功应用)")
                continue

            print(f"▶️ [正在执行] {item['filename']} - {item['description']}...")
            statements = split_sql_statements(content)
            start_time = time.time()

            try:
                with conn.cursor() as cursor:
                    for stmt in statements:
                        if stmt.strip():
                            cursor.execute(stmt)
                    
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    cursor.execute("""
                        INSERT INTO schema_version 
                        (version, description, type, script, checksum, installed_by, execution_time, success)
                        VALUES (%s, %s, 'SQL', %s, %s, %s, %s, 1)
                    """, (v, item["description"], item["filename"], checksum, DB_USER, elapsed_ms))
                conn.commit()
                migrated_count += 1
                print(f"✅ [成功应用] {item['filename']} (耗时 {elapsed_ms}ms)")
            except Exception as e:
                conn.rollback()
                elapsed_ms = int((time.time() - start_time) * 1000)
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO schema_version 
                            (version, description, type, script, checksum, installed_by, execution_time, success)
                            VALUES (%s, %s, 'SQL', %s, %s, %s, %s, 0)
                        """, (v, item["description"], item["filename"], checksum, DB_USER, elapsed_ms))
                    conn.commit()
                except Exception:
                    pass
                print(f"❌ [执行失败] {item['filename']}: {e}")
                sys.exit(1)

        print("-" * 70)
        print(f"🎉 数据库迁移完成！新应用脚本数: {migrated_count}")
        print("=" * 70)

    finally:
        conn.close()


def show_status():
    ensure_database()
    conn = get_connection(include_db=True)
    try:
        ensure_schema_version_table(conn)
        applied = get_applied_migrations(conn)
        available = parse_migration_files()

        print("=" * 70)
        print(f"📊 数据库迁移状态清单 ({DB_NAME})")
        print("=" * 70)
        print(f"{'版本':<10} | {'脚本名称':<32} | {'状态':<8} | {'应用时间'}")
        print("-" * 70)
        for item in available:
            v = item["raw_version"]
            if v in applied:
                status = "✅ SUCCESS" if applied[v]["success"] else "❌ FAILED"
            else:
                status = "⏳ PENDING"
            print(f"{v:<10} | {item['filename']:<32} | {status}")
        print("=" * 70)
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        run_migrations()
