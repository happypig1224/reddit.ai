import os
import sys
from pathlib import Path

# 标识测试环境，启用 NullPool 防止异步事件循环连接冲突
os.environ["TESTING"] = "1"

# 将项目根目录注入 sys.path，保证无论是直接调用 pytest 还是子进程执行均能解析 app 模块
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
