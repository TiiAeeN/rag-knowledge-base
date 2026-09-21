# SQL 与数据库基础

## 1. 关系型数据库基本概念
- 表（table）：二维结构，由行（记录）和列（字段）组成。
- 主键（primary key）：唯一标识一行。
- 外键（foreign key）：引用另一张表的主键，维护数据一致性。
- 约束：NOT NULL、UNIQUE、CHECK、DEFAULT。
- 常见数据库：MySQL、PostgreSQL、SQL Server、Oracle。

## 2. 查询基础
```sql
SELECT id, name, price
FROM products
WHERE price > 100 AND category = 'books'
ORDER BY price DESC
LIMIT 10 OFFSET 20;
```
- 条件运算：=、<>、>、<、BETWEEN、IN、LIKE（% 通配）、IS NULL。
- 去重：`SELECT DISTINCT category FROM products;`
- 别名：`SELECT price * 0.9 AS final_price FROM products;`

## 3. 增删改
```sql
INSERT INTO products (name, price, category)
VALUES ('Python 教程', 59.9, 'books');

UPDATE products SET price = 49.9 WHERE id = 1;

DELETE FROM products WHERE id = 2;
```
- 生产环境执行 UPDATE/DELETE 前先用 SELECT 验证条件，避免误删全表。

## 4. 聚合与分组
```sql
SELECT category, COUNT(*) AS cnt, AVG(price) AS avg_price
FROM products
WHERE price IS NOT NULL
GROUP BY category
HAVING COUNT(*) >= 3
ORDER BY cnt DESC;
```
- 常用聚合：COUNT、SUM、AVG、MAX、MIN。
- WHERE 过滤行，HAVING 过滤分组后的结果。

## 5. 连接查询
```sql
-- 内连接：只保留两表都匹配的行
SELECT o.id, u.name, o.amount
FROM orders o
INNER JOIN users u ON u.id = o.user_id;

-- 左连接：保留左表全部行，右表没有的为 NULL
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
```
- 其他：RIGHT JOIN、FULL JOIN、CROSS JOIN（笛卡尔积）、自连接。

## 6. 子查询与视图
```sql
SELECT name FROM products
WHERE price > (SELECT AVG(price) FROM products);

CREATE VIEW expensive_products AS
SELECT * FROM products WHERE price > 100;
```
- 公共表表达式（CTE）更易读：
```sql
WITH stats AS (
  SELECT category, AVG(price) AS avg_price FROM products GROUP BY category
)
SELECT * FROM stats WHERE avg_price > 100;
```

## 7. 索引
- 作用：加速查询（类似书的目录），代价是占空间、写入变慢。
- 会自动建索引的：主键、唯一约束；外键通常建议手动建。
- 适合建索引：WHERE / JOIN / ORDER BY 中频繁使用的列，区分度高的列。
- 索引失效的常见情况：对列使用函数、LIKE '%abc' 前缀通配、隐式类型转换。
- 复合索引遵循最左前缀原则。
- 用 EXPLAIN 查看执行计划，判断是否走索引。

## 8. 事务与 ACID
```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- 出错时用 ROLLBACK 回滚
```
- 原子性（Atomicity）：要么全成功，要么全失败。
- 一致性（Consistency）：数据始终满足约束。
- 隔离性（Isolation）：并发事务互不干扰；常见隔离级别：读未提交、读已提交、可重复读、串行化。
- 持久性（Durability）：提交后即使断电也不丢。
- 常见并发问题：脏读、不可重复读、幻读。

## 9. 数据库设计
- 三大范式：1NF（字段不可再分）、2NF（消除部分依赖）、3NF（消除传递依赖）。
- 反范式：为了查询性能适度冗余（如统计字段）。
- 常用字段类型：INT/BIGINT、VARCHAR/CHAR、TEXT、DATETIME/TIMESTAMP、DECIMAL（金额用定点数）。
- 规范：字段非空优先、建立 created_at/updated_at、软删除用 is_deleted 标记。

## 10. MySQL 常用命令
```sql
SHOW DATABASES;
USE mydb;
SHOW TABLES;
DESC products;
SHOW INDEX FROM products;
EXPLAIN SELECT * FROM products WHERE category = 'books';
```
```bash
mysql -u root -p mydb < backup.sql     # 导入
mysqldump -u root -p mydb > backup.sql # 备份
```

## 11. NoSQL 简介
- Redis：内存键值数据库，支持字符串/哈希/列表/集合，常用于缓存、会话、计数器。
```bash
SET user:1 "Ana"
GET user:1
EXPIRE user:1 3600
```
- MongoDB：文档数据库，存 JSON 风格文档，适合结构灵活的场景。
- 选型建议：强事务与关系复杂选关系型；高并发缓存用 Redis；日志/半结构化数据可考虑文档库。
- CAP 理论：一致性、可用性、分区容错性三者不能同时完全满足。

## 12. 性能优化建议
- 只查需要的列，避免 SELECT *。
- 用索引覆盖常见查询，减少回表。
- 分页深翻页优化：用游标（WHERE id > last_id LIMIT N）代替大 OFFSET。
- 批量写入用事务合并；避免在循环里逐条查询（N+1 问题）。
- 监控慢查询日志，定期分析执行计划。