# PHP 与 Web 后端基础

## 1. 语言特点
- PHP 是服务端脚本语言，代码直接嵌入 HTML 或由框架路由处理，请求结束即释放内存。
- 部署门槛低：搭配 Nginx/Apache + PHP-FPM 即可运行，虚拟主机普遍支持。
- 生态成熟：WordPress、Laravel、ThinkPHP、Symfony 都基于 PHP。
- 现代 PHP（8.x）已支持类型声明、命名空间、Composer 依赖管理、JIT。

## 2. 基础语法
```php
<?php
declare(strict_types=1);

$name = "PHP";
$count = 3;
$price = 9.9;

function total(float $price, int $count): float {
    return $price * $count;
}

echo "名称 {$name}，总价 " . total($price, $count) . PHP_EOL;

$fruits = ["apple", "banana", "cherry"];
foreach ($fruits as $index => $fruit) {
    echo "$index => $fruit\n";
}

$user = ["name" => "小明", "age" => 18];   // 关联数组
echo $user["name"];
```
- 变量以 `$` 开头，不需要声明类型；数组同时充当列表与哈希表。
- 字符串用单引号（不解析变量）或双引号（解析变量），拼接用 `.`。
- 常用输出：echo、print_r（调试）、var_dump（类型与值）。

## 3. 函数、类与命名空间
```php
<?php
namespace App;

class User
{
    public function __construct(
        private string $name,
        private int $age = 0,
    ) {}

    public function greet(): string
    {
        return "你好，我是 {$this->name}";
    }

    public function getAge(): int
    {
        return $this->age;
    }
}

$u = new User("小红", 20);
echo $u->greet();
```
- 类成员访问用 `->`；静态成员用 `::`。
- 接口用 interface，实现用 implements，继承用 extends（单继承）。
- 命名空间与 PSR-4 自动加载是 Composer 生态的基础。

## 4. 常用数组操作
```php
$nums = [5, 1, 4, 2, 3];

sort($nums);                                   // 原地排序
$doubled = array_map(fn($n) => $n * 2, $nums);
$evens = array_filter($nums, fn($n) => $n % 2 === 0);
$sum = array_sum($nums);
$merged = array_merge($nums, [9, 10]);
$names = array_column($users, "name");         // 取二维数组某列
$has = in_array(4, $nums, true);               // 严格比较
```
- array_map/array_filter/array_reduce 等价于其他语言的 map/filter/reduce。
- 注意：array_filter 会保留原键，需要连续下标时用 array_values。

## 5. 表单、会话与文件上传
```php
<?php
session_start();

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $email = filter_input(INPUT_POST, "email", FILTER_VALIDATE_EMAIL);

    if (!$email) {
        $error = "邮箱格式不正确";
    } else {
        $_SESSION["user"] = $email;        // 登录状态等存 session
        header("Location: /welcome.php");
        exit;
    }
}

// 文件上传
if (!empty($_FILES["avatar"]["tmp_name"])) {
    $target = __DIR__ . "/uploads/" . basename($_FILES["avatar"]["name"]);
    move_uploaded_file($_FILES["avatar"]["tmp_name"], $target);
}
```
- 永远不要直接拼接用户输入到 SQL，使用 PDO 预处理防注入。

## 6. 数据库访问（PDO）
```php
<?php
$pdo = new PDO("mysql:host=127.0.0.1;dbname=app;charset=utf8mb4", "root", "密码", [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

$stmt = $pdo->prepare("SELECT id, name FROM users WHERE age > :age LIMIT :limit");
$stmt->bindValue(":age", 18, PDO::PARAM_INT);
$stmt->bindValue(":limit", 10, PDO::PARAM_INT);
$stmt->execute();

foreach ($stmt->fetchAll() as $row) {
    echo $row["name"];
}

$pdo->beginTransaction();
try {
    $pdo->exec("UPDATE account SET balance = balance - 100 WHERE id = 1");
    $pdo->exec("UPDATE account SET balance = balance + 100 WHERE id = 2");
    $pdo->commit();
} catch (Throwable $e) {
    $pdo->rollBack();
    throw $e;
}
```

## 7. Composer 与框架
```bash
composer init                       # 初始化项目
composer require monolog/monolog     # 添加依赖
composer install                     # 按 composer.lock 安装
composer dump-autoload               # 重新生成自动加载
```
- Laravel 路由示例：`Route::get('/users/{id}', [UserController::class, 'show']);`
- 常用组件：Guzzle（HTTP 客户端）、Carbon（时间处理）、PHPUnit（测试）。

## 8. 常见陷阱
- `==` 松散比较会做类型转换（"1abc" == 1 为真），比较一律用 `===`。
- 未定义数组键会产生警告，取值前用 `??` 或 isset 判断。
- 输出用户内容必须 htmlspecialchars 转义，否则会有 XSS 漏洞。
- 浮点数不要直接比较相等，金额建议用整数分或 bcmath。