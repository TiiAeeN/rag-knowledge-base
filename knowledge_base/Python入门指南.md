# Python 入门指南

## 1. Python 简介
Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
它以其简洁的语法和强大的功能而闻名，被广泛应用于 Web 开发、数据科学、人工智能等领域。

## 2. 基本语法

### 2.1 变量和数据类型
Python 支持多种数据类型：
- 整数 (int): 如 42, -17, 0
- 浮点数 (float): 如 3.14, -0.001, 2.0
- 字符串 (str): 如 "Hello", 'World'
- 布尔值 (bool): True, False
- 列表 (list): 如 [1, 2, 3], ['a', 'b', 'c']
- 字典 (dict): 如 {'name': 'Alice', 'age': 25}

### 2.2 控制流
Python 使用缩进来定义代码块：

```python
if x > 0:
    print("正数")
elif x < 0:
    print("负数")
else:
    print("零")

for i in range(5):
    print(i)
```

### 2.3 函数定义
使用 def 关键字定义函数：

```python
def greet(name, greeting="你好"):
    '''向用户问好'''
    return f"{greeting}，{name}！"

message = greet("世界")
print(message)
```

## 3. 常用内置函数

### 3.1 数据处理
- len(): 返回对象长度
- type(): 返回对象类型
- range(): 生成数字序列

### 3.2 类型转换
- int(): 转换为整数
- float(): 转换为浮点数
- str(): 转换为字符串

## 4. 文件操作

```python
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('Hello, World!')
```

## 5. 异常处理

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零！")
except Exception as e:
    print(f"发生错误: {e}")
```

## 6. 列表推导式

```python
squares = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]
```

## 7. 类和对象

```python
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name} 说：汪汪！"

my_dog = Dog("旺财", 3)
print(my_dog.bark())
```

## 8. 最佳实践

1. **遵循 PEP 8** 编码规范
2. **编写文档字符串**
3. **使用有意义的变量名**
4. **保持函数简短专注**

---

*本文档最后更新: 2026年9月*
