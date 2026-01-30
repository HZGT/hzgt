# Smtpop 类

## 功能说明
Smtpop 是一个基于 SMTPLib 库封装的类，提供 SMTP 邮件发送功能，支持添加收件人、附件，发送普通文本和 HTML 格式的邮件。

## 初始化方法

### `__init__(self, host: str, port: int, user: str, passwd: str, logger=None)`

**参数说明：**
- `host` (str): SMTP服务器地址 例如: "smtp.qq.com"
- `port` (int): SMTP服务器端口 例如: 587
- `user` (str): 登录用户名
- `passwd` (str): 授权码
- `logger` (logging.Logger, 可选): 日志记录器

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import Smtpop

# 基本用法
smtp = Smtpop(
    host="smtp.qq.com",
    port=587,
    user="your_email@qq.com",
    passwd="your_authorization_code"
)

# 使用自定义日志记录器
smtp = Smtpop(
    host="smtp.qq.com",
    port=587,
    user="your_email@qq.com",
    passwd="your_authorization_code",
    logger=custom_logger
)
```

## 主要方法

### `login(self)`

**功能：** 登录SMTP服务器

**参数说明：**
- 无

**返回值：**
- 无

### `add_recipient(self, recipient: Union[str, Iterable[str]], *args)`

**功能：** 添加收件人

**参数说明：**
- `recipient` (str or Iterable[str]): 收件人邮箱地址或可迭代的收件人邮箱地址容器
- `*args` (str or Iterable[str]): 额外的收件人邮箱地址或可迭代的收件人邮箱地址容器

**返回值：**
- 无

**示例：**
```python
# 添加单个收件人
smtp.add_recipient("recipient1@example.com")

# 添加多个收件人
smtp.add_recipient(["recipient1@example.com", "recipient2@example.com"])

# 混合添加
smtp.add_recipient("recipient1@example.com", ["recipient2@example.com", "recipient3@example.com"])
```

### `add_file(self, file_path: str)`

**功能：** 添加附件到邮件中

**参数说明：**
- `file_path` (str): 附件文件路径

**返回值：**
- 无

**示例：**
```python
# 添加附件
smtp.add_file("path/to/file.txt")
smtp.add_file("path/to/image.jpg")
```

### `send(self, subject: str, body: str, html=False)`

**功能：** 发送邮件

**参数说明：**
- `subject` (str): 邮件主题
- `body` (str): 邮件正文
- `html` (bool, 可选): 指示邮件正文是否为HTML格式，默认为False

**返回值：**
- 无

**示例：**
```python
# 发送普通文本邮件
smtp.send(
    subject="测试邮件",
    body="这是一封测试邮件"
)

# 发送HTML格式邮件
smtp.send(
    subject="测试HTML邮件",
    body="<h1>这是一封测试HTML邮件</h1><p>邮件内容</p>",
    html=True
)
```

### `close(self)`

**功能：** 关闭SMTP连接

**参数说明：**
- 无

**返回值：**
- 无

## 上下文管理器

Smtpop 类支持上下文管理器协议，可以使用 `with` 语句自动管理连接：

```python
with Smtpop(
    host="smtp.qq.com",
    port=587,
    user="your_email@qq.com",
    passwd="your_authorization_code"
) as smtp:
    smtp.add_recipient("recipient@example.com")
    smtp.add_file("path/to/file.txt")
    smtp.send(
        subject="测试邮件",
        body="这是一封测试邮件"
    )
```

## 错误处理

Smtpop 类内部会捕获并记录邮件操作中的错误，同时提供详细的错误信息。如果需要自定义错误处理，可以通过捕获相应的异常来实现。

## 注意事项

1. 使用前需要在邮件服务提供商处获取授权码，而不是使用邮箱密码
2. 确保SMTP服务器地址和端口设置正确
3. 发送邮件前需要先登录SMTP服务器
4. 可以使用上下文管理器自动处理登录和关闭操作