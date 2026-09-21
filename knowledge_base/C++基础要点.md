# C++ 基础要点

## 1. 编译流程
- 预处理（展开 #include、#define）→ 编译（生成目标文件 .o/.obj）→ 链接（合并成可执行文件）。
- 常用编译器：g++ / clang++ / MSVC。
```bash
g++ -std=c++17 -Wall -O2 main.cpp -o app
```
- 头文件（.h/.hpp）放声明，源文件（.cpp）放实现；使用 `#pragma once` 或 include guard 防止重复包含。

## 2. 基本语法
```cpp
#include <iostream>
#include <string>

int main() {
    int count = 3;
    double price = 9.9;
    std::string name = "C++";
    const int max_size = 100;

    if (count > 0) {
        std::cout << name << " 数量: " << count << std::endl;
    }

    for (int i = 0; i < count; ++i) {
        std::cout << i << " ";
    }
    return 0;
}
```
- 常见类型：int、long long、float、double、char、bool、size_t。
- 命名空间：`std::` 表示标准库命名空间，避免全局 `using namespace std;`。

## 3. 指针与引用
```cpp
int a = 10;
int* p = &a;        // 指针：保存地址，可为空
int& r = a;         // 引用：别名，必须初始化且不可改绑
*p = 20;            // 解引用修改
std::cout << a;     // 20
```
- const 修饰：`const int* p`（指向常量的指针）、`int* const p`（常量指针）。
- 优先用引用传参避免拷贝：`void f(const std::string& s)`。

## 4. 内存管理
- 栈内存：函数局部变量，自动释放，容量小。
- 堆内存：`new` / `delete` 手动管理，容易泄漏。
- RAII：资源获取即初始化，用对象生命周期管理资源（这是 C++ 的核心思想）。
- 智能指针（现代 C++ 推荐）：
```cpp
#include <memory>

auto p1 = std::make_unique<Foo>();   // 独占所有权
auto p2 = std::make_shared<Foo>();   // 共享所有权，引用计数为 0 时释放
std::weak_ptr<Foo> w = p2;           // 不增加引用计数，解决循环引用
```

## 5. 面向对象
```cpp
class Shape {
public:
    virtual double area() const = 0;   // 纯虚函数
    virtual ~Shape() = default;        // 基类析构函数应为虚函数
};

class Circle : public Shape {
public:
    explicit Circle(double r) : radius_(r) {}
    double area() const override { return 3.14159 * radius_ * radius_; }
private:
    double radius_;
};
```
- 三大特性：封装、继承、多态（虚函数 + 基类指针/引用）。
- 构造/析构顺序：先构造基类，再构造成员；析构相反。
- 三/五法则：涉及资源管理时要考虑拷贝构造、拷贝赋值、析构（及移动版本）。

## 6. STL 常用容器
```cpp
#include <vector>
#include <map>
#include <unordered_map>
#include <algorithm>

std::vector<int> nums{3, 1, 2};
nums.push_back(4);
std::sort(nums.begin(), nums.end());

std::map<std::string, int> ordered;      // 红黑树，按 key 有序
std::unordered_map<std::string, int> fast; // 哈希表，平均 O(1)
fast["apple"] = 3;

auto it = std::find(nums.begin(), nums.end(), 2);
if (it != nums.end()) { /* 找到 */ }
```
- vector：动态数组（尾部增删快）；list/deque：特定场景使用。
- 迭代器统一了容器遍历方式，注意迭代器失效问题。
- string 是字符容器，支持 `substr`、`find`、`+`。

## 7. 现代 C++ 特性（C++11 起）
- auto 自动类型推断、范围 for：`for (const auto& x : nums)`。
- lambda 表达式：`std::sort(v.begin(), v.end(), [](int a, int b){ return a > b; });`
- nullptr 代替 NULL；constexpr 编译期常量。
- 移动语义与右值引用（std::move）：避免不必要的深拷贝。
- 结构化绑定（C++17）：`auto [key, value] = *map.begin();`

## 8. 常见陷阱
- 悬垂指针：对象已释放仍在使用。
- 数组越界访问 → 未定义行为（可能崩溃或静默出错）。
- 浅拷贝导致重复释放（double free），需要自定义拷贝或禁用拷贝。
- 忘记虚析构函数导致派生类资源泄漏。
- 整数除法截断、浮点比较用误差范围。

## 9. 构建工具（CMake 示例）
```cmake
cmake_minimum_required(VERSION 3.15)
project(demo CXX)

set(CMAKE_CXX_STANDARD 17)
add_executable(app main.cpp utils.cpp)
target_include_directories(app PRIVATE include)
```
```bash
cmake -S . -B build
cmake --build build
```

## 10. 调试与工具
- 编译器警告：`-Wall -Wextra`，把警告当错误 `-Werror`。
- 调试器：gdb / lldb / Visual Studio 调试器。
- 内存检查：valgrind、AddressSanitizer（`-fsanitize=address`）。
- 性能分析：perf、VTune、gprof。