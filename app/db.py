import os
import mysql.connector
from dotenv import load_dotenv
from flask import g

# 1) 读取 .env 文件，把 DB_HOST / DB_USER 等环境变量加载进来
load_dotenv()


def get_db():
    """
    返回一个 MySQL 连接（mysql.connector.connect 的对象）。
    关键点：把连接放进 Flask 的 g（request-scope 缓存），
    同一个 HTTP 请求里多次调用 get_db() 不会重复连接数据库。
    """
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "bike_app"),
        )
    return g.db


def close_db(e=None):
    """
    在请求结束时关闭连接。
    Flask 会在 teardown_appcontext 时调用它（我们在 app.py 里挂上）。
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

