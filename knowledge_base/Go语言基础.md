# Go 语言基础

## 1. 语言特点
- 静态类型、编译为单一可执行文件、部署简单。
- 内置并发（goroutine + channel）、垃圾回收、标准库强大。
- 语法简洁，强制格式化（gofmt），编译速度快。

## 2. 基础语法
```go
package main

import "fmt"

func main() {
    var count int = 3
    name := "Go"             // 短变量声明，自动推断类型
    const pi = 3.14

    if count > 0 {
        fmt.Println(name, count)
    }

    for i := 0; i < count; i++ {   // Go 只有 for，没有 while
        fmt.Println("第", i, "次")
    }

    switch count {
    case 1:
        fmt.Println("一个")
    default:
        fmt.Println("多个")
    }
}
```
- 基本类型：int/int64、float64、string、bool、byte、rune。
- 零值：数值为 0、字符串为空串、指针/接口/切片/map 为 nil。

## 3. 函数与错误处理
```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("除数不能为 0")
    }
    return a / b, nil
}

value, err := divide(10, 2)
if err != nil {
    fmt.Println("出错:", err)
    return
}
fmt.Println(value)
```
- 多返回值：常见形式是 (结果, error)。
- defer：函数返回前执行，常用于关闭文件、释放锁。
```go
f, err := os.Open("data.txt")
if err != nil { return }
defer f.Close()
```
- panic / recover：只用于真正的异常场景，不要当作普通错误处理。

## 4. 结构体与接口
```go
type User struct {
    Name string
    Age  int
}

func (u User) Greet() string { return "你好，" + u.Name }

type Greeter interface {
    Greet() string
}

var g Greeter = User{Name: "Ana"}
fmt.Println(g.Greet())
```
- 方法接收者：值接收者（复制）或指针接收者（可修改原值）。
- 接口是隐式实现：只要方法集匹配即可，无需显式声明。

## 5. 切片与映射
```go
nums := []int{1, 2, 3}
nums = append(nums, 4)
fmt.Println(len(nums), cap(nums), nums[1:3])

m := map[string]int{"apple": 3}
m["pear"] = 5
if v, ok := m["pear"]; ok {
    fmt.Println("pear:", v)
}
delete(m, "pear")
```
- 切片是数组的视图（长度 + 容量），注意共享底层数组的坑。
- map 必须用 make 初始化后再赋值（或使用字面量）。

## 6. 并发
```go
func worker(id int, jobs <-chan int, results chan<- int) {
    for job := range jobs {
        results <- job * 2
    }
}

jobs := make(chan int, 5)
results := make(chan int, 5)
for w := 1; w <= 3; w++ { go worker(w, jobs, results) }
for j := 1; j <= 5; j++ { jobs <- j }
close(jobs)
for r := 1; r <= 5; r++ { fmt.Println(<-results) }
```
- goroutine：`go f()` 启动轻量级线程。
- channel：goroutine 间通信，无缓冲会阻塞等待。
- sync 包：WaitGroup（等待一组任务）、Mutex（互斥锁）、Once。
- 原则：不要通过共享内存通信，而要通过通信共享内存。

## 7. 包与模块
```bash
go mod init example.com/demo   # 初始化模块，生成 go.mod
go get github.com/gin-gonic/gin  # 添加依赖
go run main.go
go build -o app.exe
go test ./...
```
- 包内可见性由首字母大小写决定：大写导出（public），小写包内私有。
- 常用目录结构：cmd/（入口）、internal/（内部包）、pkg/（可复用包）。

## 8. 标准库常用包
- fmt：格式化输入输出。
- net/http：HTTP 客户端与服务端。
- encoding/json：JSON 序列化与反序列化。
- os / io / bufio：文件与流操作。
- time：时间与定时器。
- strings / strconv：字符串处理与类型转换。
- context：超时与取消传播。

## 9. HTTP 服务示例
```go
package main

import (
    "encoding/json"
    "net/http"
)

func hello(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json; charset=utf-8")
    json.NewEncoder(w).Encode(map[string]string{"message": "你好"})
}

func main() {
    http.HandleFunc("/api/hello", hello)
    http.ListenAndServe(":8080", nil)
}
```

## 10. 测试
```go
func Add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
    if got := Add(1, 2); got != 3 {
        t.Fatalf("Add(1,2) = %d, 期望 3", got)
    }
}
```
- 文件命名 `xxx_test.go`，运行 `go test ./...`，基准测试用 `BenchmarkXxx`。