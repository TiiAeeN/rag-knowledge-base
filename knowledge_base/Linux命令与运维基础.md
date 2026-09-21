# Linux 命令与运维基础

## 1. 文件与目录
```bash
ls -alh              # 列出文件（含隐藏、详细、易读大小）
cd /var/log          # 切换目录
pwd                  # 显示当前路径
mkdir -p data/raw    # 递归创建目录
cp -r src dst        # 复制目录
mv old.txt new.txt   # 重命名或移动
rm -rf build/        # 递归删除（危险，确认路径后再执行）
find . -name "*.log" -mtime +7   # 查找 7 天前的日志
```

## 2. 查看与文本处理
```bash
cat app.log                 # 查看全部内容
less app.log                # 分页查看（q 退出，/ 搜索）
head -n 20 app.log          # 前 20 行
tail -f app.log             # 实时跟踪日志
grep -rn "ERROR" src/       # 递归搜索并显示行号
grep -c "404" access.log    # 统计匹配行数
sed 's/old/new/g' file      # 文本替换
awk '{print $1, $7}' access.log   # 按列提取
wc -l app.log               # 统计行数
sort | uniq -c | sort -rn   # 去重计数并按次数排序
```
- 管道 `|` 把上一个命令的输出交给下一个命令处理。
- 重定向：`>` 覆盖写入，`>>` 追加，`2>` 错误输出。

## 3. 权限管理
```bash
chmod 755 script.sh      # rwxr-xr-x
chmod +x script.sh       # 添加可执行权限
chown user:group file    # 修改所有者
sudo systemctl restart nginx   # 以管理员权限执行
umask                    # 查看默认权限掩码
```
- 权限位：r（读=4）、w（写=2）、x（执行=1），分别对应所有者/所属组/其他人。
- 最小权限原则：不要随意使用 777。

## 4. 进程与资源
```bash
ps aux | grep python     # 查看进程
top / htop               # 实时资源占用（q 退出）
kill -9 <pid>            # 强制结束进程（先用 kill -15 优雅退出）
nohup python app.py > app.log 2>&1 &   # 后台运行并记录日志
df -h                    # 磁盘使用情况
du -sh *                 # 当前目录各文件大小
free -h                  # 内存使用
lsof -i :8000            # 查看端口占用进程
```

## 5. 网络排查
```bash
ping example.com         # 连通性
curl -I https://api.example.com     # 查看响应头
curl -X POST -H "Content-Type: application/json" -d '{"a":1}' URL
wget https://example.com/file.zip   # 下载
ss -lntp                 # 查看监听端口（替代 netstat）
ssh user@host            # 远程登录
scp file.txt user@host:/data/       # 远程复制
dig example.com          # DNS 解析
traceroute example.com   # 路由追踪
```

## 6. 压缩与打包
```bash
tar -czvf backup.tar.gz data/     # 打包压缩
tar -xzvf backup.tar.gz           # 解压
zip -r site.zip site/             # zip 压缩
unzip site.zip
```

## 7. 环境变量与 Shell 脚本
```bash
export API_KEY=xxx                # 当前会话有效
echo $PATH                        # 查看可执行文件搜索路径
env | grep API                    # 查看所有环境变量
```
```bash
#!/usr/bin/env bash
set -euo pipefail            # 出错即退出、未定义变量报错

for file in *.log; do
    echo "处理 $file"
done

if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
fi
```
- `set -euo pipefail` 是脚本健壮性的常见起点。

## 8. 服务与定时任务
```bash
systemctl status nginx      # 查看服务状态
systemctl start/stop/restart nginx
systemctl enable nginx      # 开机自启
journalctl -u nginx -n 100  # 查看服务日志
crontab -e                  # 编辑定时任务
```
```bash
# 每天 3 点执行备份
0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```
- cron 时间格式：分 时 日 月 周。

## 9. Docker 基础
```bash
docker ps -a                       # 查看容器
docker images                      # 查看镜像
docker run -d -p 8000:8000 --name app myimage:1.0
docker logs -f app                 # 查看日志
docker exec -it app bash           # 进入容器
docker stop app && docker rm app
docker build -t myimage:1.0 .      # 构建镜像
```
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```
- 镜像分层缓存：把不常变的指令写在前面，加快构建。

## 10. 常见排查思路
1. 服务起不来：看日志（journalctl / 应用日志）→ 检查端口占用 → 检查配置与权限。
2. 磁盘满：`df -h` 定位分区 → `du -sh /*` 找大目录 → 清理日志/临时文件。
3. CPU/内存高：`top` 找进程 → 分析线程栈与堆内存 → 扩容或优化代码。
4. 网络不通：`ping` → `curl` → `ss -lntp` → 检查防火墙与安全组。
5. 权限报错：查看文件属主与权限位，必要时用 sudo 或调整 chmod/chown。