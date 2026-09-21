# HTML、CSS 与前端框架

## 1. 前端技术栈概览
- HTML：页面结构与内容（语义标签）。
- CSS：样式、布局、动画、响应式。
- JavaScript/TypeScript：交互逻辑与数据处理。
- 框架：React、Vue、Angular、Svelte；构建工具：Vite、Webpack。
- 工程化：包管理（npm/pnpm）、代码检查（ESLint）、格式化（Prettier）、单元测试（Vitest/Jest）。

## 2. HTML 基础
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>示例页面</title>
</head>
<body>
  <header>
    <h1>我的网站</h1>
    <nav>
      <a href="/">首页</a>
      <a href="/about">关于</a>
    </nav>
  </header>

  <main>
    <section>
      <h2>文章列表</h2>
      <ul>
        <li><a href="/post/1">第一篇文章</a></li>
        <li><a href="/post/2">第二篇文章</a></li>
      </ul>
    </section>

    <form action="/search" method="get">
      <label for="q">关键词</label>
      <input id="q" name="q" type="search" placeholder="输入关键词" required>
      <button type="submit">搜索</button>
    </form>

    <img src="photo.jpg" alt="风景照" width="320">
  </main>

  <footer>© 2026 示例</footer>
</body>
</html>
```
- 语义标签（header/nav/main/section/article/footer）对 SEO 与无障碍访问更好。
- 常用表单控件：input（text/password/email/checkbox/radio/file）、select、textarea。

## 3. CSS 基础
```css
:root {
  --primary: #2563eb;
  --radius: 8px;
}

.card {
  display: flex;                  /* 常用布局：flex / grid */
  gap: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: var(--radius);
  background: #fff;
  transition: transform 0.2s;
}

.card:hover { transform: translateY(-2px); }

.list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

@media (max-width: 600px) {        /* 响应式：小屏单列 */
  .list { grid-template-columns: 1fr; }
}
```
- 选择器：元素、.类、#id、[属性]、:hover/:focus 等伪类、::before/::after 伪元素。
- 布局优先用 Flex（一维）和 Grid（二维），少用 float。
- 盒模型：`box-sizing: border-box` 让 padding/border 计入宽度，避免计算混乱。
- 优先级：内联样式 > id > 类/伪类 > 元素；`!important` 应尽量避免。

## 4. JavaScript 与 DOM
```javascript
// 查询与事件
const button = document.querySelector("#load");
button.addEventListener("click", async () => {
  const res = await fetch("/api/items");
  if (!res.ok) return console.error("请求失败", res.status);
  const items = await res.json();

  const list = document.querySelector("#list");
  list.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item.name;      // 用 textContent 防 XSS
    list.appendChild(li);
  }
});
```
- DOM 操作会触发重排/重绘，批量更新时先构造片段再一次性插入。
- 现代前端一般不直接操作 DOM，而是用框架的数据驱动视图。

## 5. React 要点
```jsx
import { useEffect, useState } from "react";

function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/users")
      .then((r) => r.json())
      .then(setUsers)
      .finally(() => setLoading(false));
  }, []);                                   // 空依赖：只在挂载时执行

  if (loading) return <p>加载中…</p>;
  return (
    <ul>
      {users.map((u) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  );
}

export default UserList;
```
- 组件是函数，返回 JSX；props 向下传递，状态向上回调。
- useState 存状态，useEffect 处理副作用，useMemo/useCallback 做性能优化。
- 列表渲染必须给稳定 key，不要用数组下标（会引发错乱）。

## 6. Vue 要点
```vue
<script setup>
import { ref, onMounted, computed } from "vue";

const users = ref([]);
const count = computed(() => users.value.length);

onMounted(async () => {
  const res = await fetch("/api/users");
  users.value = await res.json();
});
</script>

<template>
  <p>共 {{ count }} 位用户</p>
  <ul>
    <li v-for="u in users" :key="u.id">{{ u.name }}</li>
  </ul>
</template>
```
- 组合式 API（script setup）用 ref/reactive 定义响应式数据，computed 定义派生数据。
- 模板指令：v-if（条件渲染）、v-for（列表）、v-model（双向绑定）、v-on/@（事件）。

## 7. 前后端交互与工程实践
- REST 风格：GET 查询、POST 新建、PUT/PATCH 更新、DELETE 删除。
- 状态码：200 成功、201 已创建、400 参数错误、401 未认证、403 无权限、404 不存在、500 服务端错误。
- CORS：跨域请求需服务端返回 Access-Control-Allow-Origin。
- 前端环境变量：`.env` + `import.meta.env.VITE_*`（Vite），不要把密钥写进前端代码。
- 性能：代码分割（动态 import）、图片懒加载、gzip/br 压缩、CDN 缓存。

## 8. 常见陷阱
- innerHTML 插入用户内容会导致 XSS，优先 textContent。
- 闭包捕获的是变量引用，循环里注册事件要用 let 或闭包工厂。
- 依赖数组写错会导致 useEffect 死循环或数据不更新。
- CSS 全局污染：用 CSS Modules / scoped / BEM 命名规范隔离样式。