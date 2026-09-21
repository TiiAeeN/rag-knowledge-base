# Python 进阶指南

## 1. 常用数据结构与操作
- 列表 list：有序可变，`append`、`extend`、`insert`、`pop`、`sort`、切片 `lst[1:3]`。
- 元组 tuple：有序不可变，可作字典键。
- 字典 dict：键值对，`get`、`setdefault`、`items()`、字典推导式。
- 集合 set：去重与集合运算，`|` 并集、`&` 交集、`-` 差集。
- 推导式（列表/字典/集合）比循环更简洁高效：
```python
squares = [x * x for x in range(10)]
even = {x: x * x for x in range(10) if x % 2 == 0}
```

## 2. 函数进阶
```python
def func(a, b=1, *args, **kwargs):
    """动态参数：args 为多余位置参数，kwargs 为多余关键字参数"""
    return a + b
```
- 闭包：内部函数引用外部函数的变量。
- 装饰器：在不修改原函数的前提下增加功能（日志、计时、鉴权）。
```python
import functools, time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 耗时 {time.time() - start:.3f}s")
        return result
    return wrapper
```

## 3. 迭代器与生成器
- 生成器用 `yield` 逐个产出数据，惰性求值，适合处理大文件或大数据。
```python
def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip()
```
- 生成器表达式：`(x * 2 for x in range(1000000))`。

## 4. 异常处理
```python
try:
    value = int(text)
except ValueError as exc:
    print(f"转换失败: {exc}")
else:
    print("成功", value)
finally:
    print("总会执行")
```
- 自定义异常：继承 `Exception`，用于区分业务错误。
- 原则：只捕获能处理的异常，不要用裸 `except` 吞掉错误。

## 5. 类型注解与数据类
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int = 0

def greet(user: User) -> str:
    return f"你好，{user.name}"
```
- 类型注解不影响运行，但配合 mypy / IDE 能提前发现错误。

## 6. 上下文管理器
```python
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("hello")
```
- 自定义上下文管理器实现 `__enter__` / `__exit__`，或用 `contextlib.contextmanager`。

## 7. 模块、包与虚拟环境
- 模块：一个 .py 文件；包：含 `__init__.py` 的目录。
- 虚拟环境隔离依赖：
```bash
python -m venv .venv            # 创建
.venv\Scripts\activate          # Windows 激活
pip install -r requirements.txt # 安装依赖
pip freeze > requirements.txt   # 导出依赖
```
- 常用工具：pip、uv（更快的现代包管理器）、poetry。

## 8. 常用标准库
- `pathlib`：面向对象的路径操作，`Path("a") / "b.txt"`。
- `json`：`json.loads` / `json.dumps(ensure_ascii=False)`。
- `datetime`：时间处理，注意时区（zoneinfo）。
- `re`：正则匹配、替换、分组。
- `collections`：`defaultdict`、`Counter`、`deque`。
- `itertools`：`chain`、`groupby`、`combinations`。
- `os` / `sys` / `subprocess`：系统与进程操作。

## 9. 并发基础
- 多线程 threading：适合 IO 密集，受 GIL 影响不适合纯计算。
- 多进程 multiprocessing：适合 CPU 密集，绕开 GIL。
- 异步 asyncio：单线程事件循环，适合高并发网络请求。
```python
import asyncio

async def fetch(name):
    await asyncio.sleep(1)
    return name

async def main():
    results = await asyncio.gather(fetch("a"), fetch("b"))
    print(results)

asyncio.run(main())
```

## 10. 测试（pytest）
```python
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
```
- 运行：`pytest -q`；常用插件：pytest-cov（覆盖率）、pytest-mock。

## 11. 常用第三方库
- 网络请求：requests、httpx。
- 数据处理：numpy、pandas。
- Web 框架：FastAPI（异步、自动生成文档）、Flask（轻量）、Django（全功能）。
- 爬虫解析：BeautifulSoup、lxml。
- 数据库：SQLAlchemy（ORM）、psycopg（PostgreSQL）、pymysql（MySQL）。

## 12. 性能与风格建议
- 字符串拼接优先用 `join` 或 f-string，避免循环里反复 `+`。
- 大数据用生成器代替一次性列表。
- 循环内少做重复计算，可用 `functools.lru_cache` 缓存。
- 遵循 PEP 8；用 black / ruff 自动格式化与检查。