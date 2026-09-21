# Java 基础指南

## 1. 语言特点
- 面向对象、强类型、跨平台（一次编译，处处运行，依赖 JVM 字节码）。
- 开发流程：源码 .java → 编译 `javac` → 字节码 .class → `java` 运行。
- 生态庞大：Spring、Maven、Gradle、Hadoop/Spark 等。

## 2. 基本语法
```java
public class Demo {
    public static void main(String[] args) {
        int count = 3;
        double price = 9.9;
        boolean ok = true;
        String name = "Java";

        if (count > 0 && ok) {
            System.out.println(name + " 数量: " + count);
        }

        for (int i = 0; i < count; i++) {
            System.out.println("第 " + i + " 次");
        }

        switch (count) {
            case 1 -> System.out.println("一个");
            default -> System.out.println("多个");
        }
    }
}
```
- 八种基本类型：byte、short、int、long、float、double、char、boolean。
- 包装类型：Integer、Double 等，支持泛型与 null。

## 3. 面向对象
- 类与对象：`new` 创建实例，构造方法初始化。
- 继承：`extends`，方法重写 `@Override`。
- 接口：`interface` 定义能力，类用 `implements` 实现，支持多实现。
- 抽象类：不能被实例化，用于共享部分实现。
- 多态：父类引用指向子类对象，运行时决定调用哪个实现。
- 修饰符：public / protected / private / 默认（包内可见）；static、final。

```java
public interface Shape {
    double area();
}

public class Circle implements Shape {
    private final double radius;
    public Circle(double radius) { this.radius = radius; }
    @Override public double area() { return Math.PI * radius * radius; }
}
```

## 4. 集合框架
```java
List<String> list = new ArrayList<>();
list.add("a");
list.add("b");

Map<String, Integer> map = new HashMap<>();
map.put("apple", 3);
int value = map.getOrDefault("pear", 0);

Set<String> set = new HashSet<>(list);   // 去重
```
- List：有序可重复（ArrayList 查快，LinkedList 增删快）。
- Set：不可重复（HashSet、TreeSet）。
- Map：键值对（HashMap、TreeMap）。遍历用 `entrySet()`。
- 线程安全集合：ConcurrentHashMap、CopyOnWriteArrayList。

## 5. 异常处理
```java
try (var reader = Files.newBufferedReader(path)) {   // try-with-resources 自动关闭
    String line = reader.readLine();
} catch (IOException | RuntimeException exc) {
    System.err.println("读取失败: " + exc.getMessage());
} finally {
    System.out.println("结束");
}
```
- 受检异常（checked）：编译期必须处理，如 IOException。
- 非受检异常（unchecked）：RuntimeException 及其子类。
- 自定义异常：继承 Exception 或 RuntimeException。

## 6. 泛型、Lambda 与 Stream
```java
List<String> names = List.of("amy", "bob", "cindy");

List<String> upper = names.stream()
        .filter(n -> n.length() > 2)
        .map(String::toUpperCase)
        .sorted()
        .toList();

int total = names.stream().mapToInt(String::length).sum();
```
- Optional 用于避免空指针：`Optional.ofNullable(x).orElse("默认")`。

## 7. 常用类
- String / StringBuilder：频繁拼接用 StringBuilder。
- Files / Paths：文件读写，`Files.readString(path)`。
- LocalDate / LocalDateTime：日期时间（线程安全）。
- Math、Random、Objects、Collections。

## 8. 多线程简述
```java
ExecutorService pool = Executors.newFixedThreadPool(4);
Future<Integer> future = pool.submit(() -> 1 + 1);
System.out.println(future.get());
pool.shutdown();
```
- 关键词：synchronized、volatile、锁、线程池；高并发优先用工具类而非手写锁。

## 9. 构建与依赖
- Maven：`pom.xml` 管理依赖与构建，常用命令 `mvn clean package`。
- Gradle：`build.gradle`，更灵活的构建脚本。
- 依赖坐标：groupId / artifactId / version。

## 10. Spring Boot 简介
```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public User get(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    public User create(@RequestBody User user) {
        return userService.save(user);
    }
}
```
- 依赖注入（DI）与面向切面（AOP）是核心思想。
- 常见注解：@Component、@Service、@Repository、@Autowired、@Transactional。

## 11. JVM 简述
- 内存区域：堆（对象）、栈（方法调用）、方法区/元空间、程序计数器。
- 垃圾回收：自动回收不可达对象；常见收集器 G1、ZGC。
- 调优关注：堆大小、GC 频率与停顿、内存泄漏排查（jmap、jstack、visualvm）。