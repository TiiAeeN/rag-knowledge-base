# JavaScript 与 TypeScript 基础

## 1. 变量与类型
```javascript
let count = 1;        // 可重新赋值
const name = "Tom";   // 常量，不可重新赋值
var legacy = true;    // 旧写法，避免使用
```
- 基本类型：number、string、boolean、null、undefined、symbol、bigint。
- 引用类型：object、array、function。
- 判断类型：`typeof value`；数组用 `Array.isArray(x)`。

## 2. 函数与语法糖
```javascript
function add(a, b) { return a + b; }
const add2 = (a, b) => a + b;                 // 箭头函数
const msg = `你好，${name}，共 ${count} 条`;   // 模板字符串

const { title, price = 0 } = product;         // 解构
const merged = { ...defaults, ...options };   // 展开运算
```

## 3. 数组常用方法
```javascript
const nums = [1, 2, 3, 4];
nums.map(n => n * 2);          // [2, 4, 6, 8]
nums.filter(n => n % 2 === 0); // [2, 4]
nums.reduce((sum, n) => sum + n, 0); // 10
nums.find(n => n > 2);         // 3
nums.includes(3);              // true
```

## 4. 对象与 JSON
```javascript
const user = { name: "Ana", age: 20 };
const text = JSON.stringify(user);        // 转字符串
const obj = JSON.parse(text);             // 转对象
Object.keys(user); Object.values(user); Object.entries(user);
```

## 5. 异步编程
```javascript
// Promise
fetch("/api/users")
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

// async / await（推荐）
async function load() {
  try {
    const res = await fetch("/api/users");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("请求失败", err);
  }
}
```
- 事件循环：同步代码先执行，异步任务放入队列，等当前调用栈清空后再执行。
- 并行请求：`await Promise.all([p1, p2])`。

## 6. 模块化
```javascript
// utils.js
export function double(n) { return n * 2; }

// main.js
import { double } from "./utils.js";
```

## 7. DOM 与事件（浏览器）
```javascript
const btn = document.querySelector("#submit");
btn.addEventListener("click", () => {
  const input = document.querySelector("#name");
  document.querySelector("#out").textContent = `你好，${input.value}`;
});
```

## 8. 错误处理
```javascript
try {
  risky();
} catch (err) {
  console.error(err.message);
} finally {
  cleanup();
}
```

## 9. TypeScript 要点
```typescript
interface User {
  id: number;
  name: string;
  email?: string;          // 可选属性
}

function greet(user: User): string {
  return `你好，${user.name}`;
}

type Status = "todo" | "doing" | "done";   // 联合类型

function identity<T>(value: T): T {        // 泛型
  return value;
}
```
- 类型收窄：`typeof`、`instanceof`、可选链 `?.`、空值合并 `??`。
- 接口（interface）描述对象结构，类型别名（type）更灵活。
- 编译：`tsc`；配置 `tsconfig.json`（strict 建议开启）。

## 10. 工程工具
- 包管理：npm / yarn / pnpm，`package.json` 记录依赖与脚本。
```bash
npm init -y
npm install axios
npm run dev
```
- 构建工具：Vite（快，适合新项目）、Webpack（生态成熟）。
- 代码质量：ESLint（检查）、Prettier（格式化）。
- Node.js：服务端运行时，内置 `fs`、`path`、`http` 等模块。
```javascript
import fs from "node:fs";
fs.writeFileSync("log.txt", "hello", "utf-8");
```

## 11. 常见陷阱
- `==` 会隐式转换类型，比较请用 `===`。
- `this` 取决于调用方式，箭头函数不绑定自己的 `this`。
- 数组/对象的浅拷贝：`[...arr]`、`{...obj}` 只复制第一层。
- 浮点精度：`0.1 + 0.2 !== 0.3`，金额计算用整数或专用库。