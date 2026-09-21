# Rust 语言基础

## 1. 语言特点
- 内存安全：用所有权（ownership）+ 借用检查（borrow checker）在编译期保证安全，不需要垃圾回收。
- 零成本抽象：迭代器、泛型、trait 编译后与手写底层代码性能接近。
- 并发安全：编译器区分 Send/Sync，数据竞争在编译期就会被拦下。
- 工具链：rustup 安装、cargo 负责构建/依赖/测试/发布。
- 常见用途：系统编程、命令行工具、WebAssembly、高性能网络服务、嵌入式。

## 2. 基础语法
```rust
fn main() {
    let name = "Rust";          // 默认不可变
    let mut count: i32 = 3;     // 加 mut 才可修改
    count += 1;
    println!("{name} 第 {count} 次");

    let (a, b) = (1, 2.5);      // 元组解构
    let nums = [1, 2, 3];       // 定长数组
    println!("{} {}", a, b + nums[0] as f64);
}
```
- 标量类型：i32/u32/i64/u64、f32/f64、bool、char（4 字节 Unicode）。
- 复合类型：元组 (T1, T2)、数组 [T; N]、切片 &[T]。
- 表达式语言：`if`、`match`、代码块都有返回值，`let x = if ok { 1 } else { 2 };`。

## 3. 所有权、借用与生命周期
```rust
fn length(s: &str) -> usize {   // 借用 &str，不夺走所有权
    s.len()
}

fn main() {
    let s = String::from("hello");
    let n = length(&s);          // 借用，s 仍然可用
    let moved = s;               // 移动：此后 s 不能再使用
    println!("{n} {}", moved.len());
}
```
- 规则：每个值只有一个所有者；所有者离开作用域，值自动释放。
- 借用分两种：`&T` 只读可多个，`&mut T` 可写但同一时刻只能有一个。
- 生命周期标注 `fn longest<'a>(a: &'a str, b: &'a str) -> &'a str` 用于告诉编译器返回的引用活得够久。

## 4. 错误处理
```rust
use std::fs;

fn read_len(path: &str) -> Result<usize, std::io::Error> {
    let content = fs::read_to_string(path)?;   // ? 出错直接返回
    Ok(content.len())
}

fn main() {
    match read_len("data.txt") {
        Ok(len) => println!("长度 {len}"),
        Err(e) => println!("读取出错: {e}"),
    }
}
```
- `Result<T, E>` 表示可能失败；`Option<T>` 表示可能为空（Some/None）。
- `?` 运算符是错误传播的语法糖；`unwrap()/expect()` 只适合确定不会失败的场景。
- `panic!` 用于不可恢复错误，会终止线程。

## 5. 结构体、枚举与模式匹配
```rust
struct User {
    name: String,
    age: u32,
}

enum Shape {
    Circle(f64),
    Rect(f64, f64),
}

fn area(shape: &Shape) -> f64 {
    match shape {
        Shape::Circle(r) => 3.14159 * r * r,
        Shape::Rect(w, h) => w * h,
    }
}

impl User {
    fn new(name: &str, age: u32) -> Self {
        Self { name: name.to_string(), age }
    }
}
```
- `match` 必须覆盖所有分支，可以用 `_ => ()` 兜底。
- `if let Some(v) = opt { ... }` 只关心一种情况时更简洁。

## 6. 集合与迭代器
```rust
use std::collections::HashMap;

let mut nums = vec![5, 1, 4, 2, 3];
nums.sort();
let squares: Vec<i32> = nums.iter().map(|n| n * n).filter(|n| n % 2 == 0).collect();

let mut scores = HashMap::new();
scores.insert("alice", 90);
scores.entry("bob").or_insert(60);       // 不存在才插入
let alice = scores.get("alice").copied().unwrap_or(0);
```
- 常用集合：Vec<T>（动态数组）、HashMap<K,V>、HashSet<T>、String。
- 迭代器是惰性的，`collect()` / `sum()` / `for` 才真正执行。

## 7. Trait 与泛型
```rust
trait Greet {
    fn hello(&self) -> String;
}

impl Greet for User {
    fn hello(&self) -> String {
        format!("你好，我是 {}", self.name)
    }
}

fn print_all<T: Greet>(items: &[T]) {
    for item in items {
        println!("{}", item.hello());
    }
}
```
- trait 类似其他语言的接口，但可以为已有类型实现（包括标准库类型）。
- 常见派生：`#[derive(Debug, Clone, PartialEq)]`。

## 8. 并发
```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..4 {
    let counter = Arc::clone(&counter);
    handles.push(thread::spawn(move || {
        let mut n = counter.lock().unwrap();
        *n += 1;
    }));
}
for h in handles { h.join().unwrap(); }
println!("{}", *counter.lock().unwrap());
```
- 线程间通信也可以用 channel：`let (tx, rx) = std::sync::mpsc::channel();`
- Arc = 原子引用计数（多线程共享所有权），Mutex = 互斥锁。

## 9. Cargo 工程
```bash
cargo new myapp          # 新建项目（含 Cargo.toml 与 src/main.rs）
cargo run                # 编译并运行
cargo build --release    # 发布版编译（开启优化）
cargo test               # 运行测试
cargo add serde --features derive   # 添加依赖
cargo fmt && cargo clippy           # 格式化与静态检查
```
- 依赖写在 Cargo.toml 的 [dependencies]，Cargo.lock 锁定精确版本。

## 10. 常见陷阱
- 借用冲突报错（cannot borrow as mutable）：同作用域内不要同时持有可变与不可变借用。
- String 与 &str：String 拥有数据可增长，&str 是借用的字符串切片，函数参数优先用 &str。
- 循环中移动所有权的值要用引用（`&item`）或 clone。
- 大量 unwrap 会让程序在意外输入时崩溃，生产代码应返回 Result。