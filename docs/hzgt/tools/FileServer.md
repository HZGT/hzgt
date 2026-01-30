# FileServer.py 文档

## 导航目录

- [Fileserver()](#fileserver)

## 函数说明

### Fileserver()

**功能**：快速构建文件服务器，支持文件浏览、下载和上传功能。

**参数**：
- `path` (str)：工作目录(共享目录路径)，默认为当前目录 "."
- `host` (str)：IP 地址，默认为本地计算机的IP地址 "::"
- `port` (int)：端口，默认为5001
- `bool_https` (bool)：是否启用HTTPS，默认为False
- `certfile` (str)：SSL证书文件路径，默认同目录下的 cert.pem
- `keyfile` (str)：SSL私钥文件路径，默认同目录下的 privkey.pem

**返回值**：`HTTPServer` 实例 - 文件服务器实例

**使用示例**：

```python
from hzgt.tools import Fileserver

# 在当前目录启动文件服务器
Fileserver()

# 在指定目录启动文件服务器，使用指定端口
Fileserver(path="/path/to/share", port=8080)

# 在指定IP和端口启动文件服务器
Fileserver(host="192.168.1.100", port=8080)

# 启用HTTPS的文件服务器
Fileserver(bool_https=True, certfile="server.crt", keyfile="server.key")
```

**完整使用示例**：

```python
from hzgt.tools import Fileserver

print("启动文件服务器...")
print("使用 Ctrl+C 停止服务器")

# 启动文件服务器
server = Fileserver(
    path=".",  # 共享当前目录
    host="0.0.0.0",  # 允许所有网络接口访问
    port=5001  # 使用5001端口
)
```

**功能特性**：

1. **文件浏览**：在浏览器中查看目录结构和文件列表
2. **文件下载**：点击文件即可下载
3. **文件上传**：支持通过浏览器上传文件到服务器
4. **路径导航**：通过导航快速切换目录
5. **响应式设计**：适配不同屏幕尺寸
6. **支持HTTPS**：可配置启用安全的HTTPS连接
7. **多网络协议支持**：支持IPv4和IPv6

**使用方法**：

1. 启动文件服务器后，在浏览器中访问显示的地址
2. 在文件服务器页面中，您可以：
   - 点击文件夹进入子目录
   - 点击文件下载文件
   - 使用页面顶部的上传表单上传文件
   - 点击路径导航中的文件夹名称快速返回上级目录

**注意事项**：

- 文件服务器默认在后台线程运行，不会阻塞主线程
- 上传的文件会保存在当前浏览的目录中
- 请确保您有足够的权限访问指定的共享目录
- 启用HTTPS时，需要提供有效的SSL证书和私钥文件
- 在生产环境中使用时，建议配置适当的访问控制和安全措施