# C# 与 .NET 基础

## 1. 语言与平台
- C#：微软推出的面向对象语言，语法接近 Java，但特性更丰富（属性、LINQ、async/await、record）。
- .NET：C# 的运行平台。.NET 6/7/8 之后跨平台，可在 Windows、Linux、macOS 上运行。
- 执行流程：C# 源码 → 编译成 IL 中间语言 → CLR 运行时 JIT 编译成本机代码执行。
- 常见用途：ASP.NET Core 后端服务、Windows 桌面（WPF/WinForms）、Unity 游戏开发、企业级系统。

## 2. 基础语法
```csharp
using System;

class Program
{
    static void Main()
    {
        int count = 3;
        double price = 9.9;
        string name = "C#";
        bool ok = true;
        var list = new List<int> { 1, 2, 3 };   // var 自动推断类型
        int? maybe = null;                       // 可空值类型

        Console.WriteLine($"名称 {name}，数量 {count}，总价 {price * count}");

        foreach (var n in list)
        {
            if (n % 2 == 0)
                Console.WriteLine($"{n} 是偶数");
        }
    }
}
```
- 值类型：int、long、double、decimal、bool、char、struct、enum（存在栈上，赋值即复制）。
- 引用类型：class、string、数组、interface、delegate（赋值是复制引用）。
- 字符串插值 `$"..."` 比字符串拼接更易读。

## 3. 面向对象与常用特性
```csharp
public interface IShape
{
    double Area();
}

public class Circle : IShape
{
    public double Radius { get; set; }        // 自动属性
    public Circle(double radius) => Radius = radius;
    public double Area() => Math.PI * Radius * Radius;
}

public record User(string Name, int Age);     // record：不可变数据载体
```
- 属性（Property）替代 Java 的 getter/setter，`{ get; set; }` 即自动实现。
- record 自带值相等比较与 ToString，适合做 DTO。
- 模式匹配：`if (obj is Circle c) { ... }`、`switch` 表达式。

## 4. 集合与 LINQ
```csharp
var nums = new List<int> { 5, 1, 4, 2, 3 };
var result = nums
    .Where(n => n % 2 == 1)      // 过滤
    .OrderBy(n => n)             // 排序
    .Select(n => n * 10)         // 映射
    .ToList();                   // 1 之后是 10 30 50

var dict = new Dictionary<string, int> { ["apple"] = 3 };
if (dict.TryGetValue("apple", out var cnt))
    Console.WriteLine(cnt);
```
- 常用集合：List<T>、Dictionary<K,V>、HashSet<T>、Queue<T>、Stack<T>。
- LINQ 是延迟执行：不调用 ToList/ToArray 就不会真正遍历。

## 5. 异常与资源释放
```csharp
try
{
    using var reader = new StreamReader("data.txt");   // 离开作用域自动 Dispose
    var text = reader.ReadToEnd();
}
catch (FileNotFoundException ex)
{
    Console.WriteLine($"文件不存在: {ex.Message}");
}
catch (Exception ex)
{
    Console.WriteLine($"其他错误: {ex.Message}");
}
finally
{
    Console.WriteLine("清理完成");
}
```
- 只捕获能处理的异常，避免裸 `catch (Exception) { }` 吞掉错误。
- `using` 等价于 try/finally + Dispose，用于文件、数据库连接、HttpClient。

## 6. 异步编程（async / await）
```csharp
public async Task<string> FetchAsync(string url)
{
    using var client = new HttpClient();
    string body = await client.GetStringAsync(url);   // 不阻塞线程
    return body.Length > 100 ? body[..100] : body;
}
```
- 返回 Task / Task<T>；async void 只用于事件处理器。
- 死锁常见原因：在同步代码里调用 `.Result` 或 `.Wait()`。

## 7. ASP.NET Core 最小 API 示例
```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/api/hello/{name}", (string name) => $"你好, {name}");

app.MapPost("/api/users", (User user) => Results.Ok(user));

app.Run();
```
- `dotnet run` 启动，默认监听 5000/7000 端口。
- 依赖注入内置：`builder.Services.AddSingleton<IService, Service>()`。

## 8. 构建与依赖管理（dotnet CLI）
```bash
dotnet new console -o HelloApp    # 新建控制台项目
dotnet new webapi -o MyApi        # 新建 Web API 项目
dotnet run                        # 编译并运行
dotnet build                      # 只编译
dotnet test                       # 运行单元测试
dotnet add package Newtonsoft.Json  # 添加 NuGet 依赖
dotnet publish -c Release -o out  # 发布部署包
```

## 9. 常见陷阱
- string 不可变，循环里大量 `+=` 应改用 StringBuilder。
- `==` 对 string 比较内容（已重载），对普通类默认比较引用。
- 值类型装箱（object o = 1）有性能开销，泛型集合可避免。
- 忘记释放 IDisposable 资源会泄漏连接和文件句柄，优先用 using。