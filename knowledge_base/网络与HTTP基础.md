# 网络与 HTTP 基础

## 1. 网络分层与常见协议
- 应用层：HTTP/HTTPS、DNS、SMTP、WebSocket、SSH。
- 传输层：TCP（可靠、面向连接）、UDP（无连接、低延迟）。
- 网络层：IP（寻址与路由）、ICMP（ping 用的协议）。
- 链路层：以太网、Wi-Fi。
- 一次网页访问的大致流程：DNS 解析域名 → TCP 三次握手 → TLS 握手（HTTPS）→ 发送 HTTP 请求 → 服务端响应 → 浏览器渲染。

## 2. TCP 与 UDP
- TCP 三次握手：SYN → SYN+ACK → ACK；四次挥手断开连接。
- TCP 保证顺序与重传，适合网页、文件传输、数据库；UDP 不保证可靠，适合直播、游戏、DNS。
- 长连接与心跳：HTTP/1.1 keep-alive、WebSocket ping/pong。
- 常见排查：连接超时（网络/防火墙）、连接被拒绝（端口未监听）、连接重置（服务崩溃或被中间设备拦截）。

## 3. HTTP 请求与响应
```http
GET /api/users?page=2 HTTP/1.1
Host: example.com
Accept: application/json
Authorization: Bearer <token>
User-Agent: curl/8.0

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Cache-Control: max-age=60

{"items":[{"id":1,"name":"小明"}],"page":2}
```
- 方法语义：GET 查询（幂等）、POST 新建、PUT 全量更新（幂等）、PATCH 局部更新、DELETE 删除。
- 常见请求头：Content-Type（请求体格式）、Authorization（认证）、Accept（期望返回格式）、Cookie。
- 常见响应头：Content-Type、Content-Length、Cache-Control、Set-Cookie、Location（重定向）。

## 4. 状态码速查
- 1xx 信息：100 Continue、101 Switching Protocols（WebSocket 升级）。
- 2xx 成功：200 OK、201 Created、204 No Content。
- 3xx 重定向：301 永久、302 临时、304 Not Modified（走缓存）。
- 4xx 客户端错误：400 参数错误、401 未认证、403 无权限、404 不存在、405 方法不允许、429 请求过于频繁。
- 5xx 服务端错误：500 内部错误、502 网关错误（后端无响应）、503 服务不可用、504 网关超时。

## 5. RESTful API 设计要点
```json
// GET /api/v1/users?page=1&size=20&sort=-created_at
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [{"id": 1, "name": "小明", "created_at": "2026-01-01T10:00:00Z"}],
    "total": 128,
    "page": 1,
    "size": 20
  }
}
```
- 用名词复数表示资源（/users、/orders），动作用 HTTP 方法表达。
- 版本号放路径（/api/v1/）便于演进；错误响应要能定位问题（错误码 + 描述）。
- 分页、排序、过滤统一用查询参数；大文件用分片或对象存储直传。

## 6. HTTPS 与安全
- HTTPS = HTTP + TLS：加密传输、校验服务器身份、防止内容被篡改。
- 证书由 CA 签发，Let's Encrypt 可免费申请并自动续期（certbot）。
- 常见攻击与防护：
  - XSS：输出转义、内容安全策略 CSP。
  - SQL 注入：参数化查询，不拼接 SQL。
  - CSRF：同源校验、CSRF Token、SameSite Cookie。
  - 中间人攻击：强制 HTTPS、HSTS。
- 密码存储必须加盐哈希（bcrypt/argon2），不要明文或简单 MD5。

## 7. 抓包与调试工具
```bash
curl -i https://example.com/api/users          # 查看响应头
curl -X POST -H "Content-Type: application/json" -d '{"name":"小明"}' https://example.com/api/users
curl -I https://example.com                    # 只看响应头
ping example.com && traceroute example.com     # 连通性与路由
dig example.com +short                          # DNS 解析
openssl s_client -connect example.com:443       # 查看证书
```
- 浏览器开发者工具：Network 面板看请求耗时、请求头、响应体；Preserve log 保留跳转记录。
- Postman/Apifox 适合接口调试与团队共享；Wireshark 用于底层抓包分析。

## 8. 性能与优化
- 减少请求数：合并资源、HTTP/2 多路复用、雪碧图或图标字体。
- 缓存：强缓存（Cache-Control: max-age）+ 协商缓存（ETag/Last-Modified）。
- 压缩：gzip / brotli；内容分块传输（Transfer-Encoding: chunked）。
- CDN 把静态资源放到离用户最近的节点；DNS 预解析与预连接可减少首包时间。
- 超时与重试：客户端设置连接/读取超时，重试要加退避并注意幂等性。

## 9. 常见排查思路
- 域名解析不通：dig/nslookup 检查 DNS 与 hosts。
- 端口不通：telnet/curl -v 测试，检查防火墙、安全组、服务监听地址（0.0.0.0 还是 127.0.0.1）。
- 502/504：查看反向代理日志与后端进程状态，确认上游地址与超时配置。
- 偶发超时：看连接数、线程池、慢 SQL、GC 停顿，用耗时打点定位瓶颈。
- HTTPS 报错：证书链不完整、域名不匹配、证书过期是三大常见原因。