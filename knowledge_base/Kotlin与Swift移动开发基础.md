# Kotlin 与 Swift 移动开发基础

## 1. 移动开发概览
- Android 主流语言：Kotlin（官方首选）、Java（历史项目）；UI 用 Jetpack Compose 或 XML 布局。
- iOS 主流语言：Swift（官方首选）、Objective-C（历史项目）；UI 用 SwiftUI 或 UIKit。
- 跨平台方案：Flutter（Dart）、React Native（JavaScript/TypeScript）、Kotlin Multiplatform。
- 打包：Android → APK/AAB（签名后上架 Google Play/国内应用市场）；iOS → IPA（需 Apple 开发者账号）。

## 2. Kotlin 基础语法
```kotlin
fun main() {
    val name: String = "Kotlin"     // val 不可变
    var count = 3                    // var 可变，类型自动推断
    count += 1

    println("$name 第 $count 次")

    val score = 85
    val level = when {              // when 表达式
        score >= 90 -> "优秀"
        score >= 60 -> "及格"
        else -> "不及格"
    }
    println(level)
}
```
- 一切皆对象，没有基本类型的概念（Int/String 都是类）。
- 可空类型：`var s: String? = null`，使用时需 `s?.length` 或 `s!!`（不推荐）。
- 字符串模板 `$变量` 与 `${表达式}`。

## 3. Kotlin 函数、类与数据类
```kotlin
data class User(val name: String, var age: Int)   // 自动生成 equals/hashCode/toString

fun greet(user: User, prefix: String = "你好"): String = "$prefix, ${user.name}"

fun List<Int>.evens(): List<Int> = filter { it % 2 == 0 }   // 扩展函数

class Repository(private val api: ApiService) {
    suspend fun load(): List<User> = api.fetchUsers()       // 挂起函数（协程）
}
```
- 顶层函数/属性不需要类包裹，`object` 声明单例。
- 协程（Coroutine）是官方异步方案：`viewModelScope.launch { ... }`。

## 4. Android 开发要点（Jetpack Compose）
```kotlin
@Composable
fun Greeting(name: String) {
    Text(text = "你好, $name", modifier = Modifier.padding(16.dp))
}

@Composable
fun UserList(users: List<User>) {
    LazyColumn {
        items(users) { user ->
            ListItem(headlineContent = { Text(user.name) })
        }
    }
}
```
- 四大组件：Activity（页面）、Service（后台）、BroadcastReceiver（广播）、ContentProvider（数据共享）。
- 网络请求常用 Retrofit + OkHttp + kotlinx.serialization。
- 本地存储：DataStore/SharedPreferences（键值）、Room（SQLite ORM）。
- 权限：网络请求要在 AndroidManifest.xml 声明 `android.permission.INTERNET`；敏感权限需运行时申请。

## 5. Swift 基础语法
```swift
import Foundation

let name = "Swift"        // let 常量
var count = 3             // var 变量
count += 1

print("\(name) 第 \(count) 次")

let score = 85
switch score {
case 90...:  print("优秀")
case 60..<90: print("及格")
default:     print("不及格")
}

func greet(_ name: String, prefix: String = "你好") -> String {
    "\(prefix), \(name)"      // 单表达式函数可省略 return
}

struct User: Codable {        // 值类型，自动支持 JSON 编解码
    let name: String
    var age: Int
}
```
- 可选类型：`var s: String? = nil`，用 `if let s = s { }` 或 `s ?? "默认值"` 解包。
- 值类型 struct 与引用类型 class：默认优先用 struct。
- 协议（protocol）类似接口，可配合扩展（extension）给已有类型加方法。

## 6. iOS 开发要点（SwiftUI）
```swift
struct ContentView: View {
    @State private var count = 0

    var body: some View {
        VStack(spacing: 12) {
            Text("点击次数: \(count)")
            Button("点我") { count += 1 }
        }
        .padding()
    }
}
```
- 状态管理：@State（视图内部）、@Observable/@StateObject（模型）、@Binding（父子传递）。
- 列表用 List + ForEach；导航用 NavigationStack。
- 网络请求用 URLSession + async/await，JSON 解析用 Codable。

## 7. 移动开发通用实践
- 分层架构：UI 层（Compose/SwiftUI）→ 状态/ViewModel 层 → 数据层（网络+数据库）。
- 生命周期：Android Activity 重建、iOS 视图刷新，都需要把状态放在可持久化的层。
- 列表性能：长列表要用懒加载（LazyColumn/List），避免在 UI 线程做耗时操作。
- 调试：Android Studio Logcat / Layout Inspector；Xcode 预览与 Instruments。

## 8. 上架与构建
```bash
# Android
./gradlew assembleRelease       # 生成签名 APK
./gradlew bundleRelease         # 生成 AAB
# iOS
xcodebuild -scheme MyApp archive
```
- Android 用 keystore 签名，密钥丢失将无法更新应用。
- iOS 需要证书 + Provisioning Profile，或使用 TestFlight 分发测试。