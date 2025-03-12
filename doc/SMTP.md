
---
`类[class]: Smtpop()`
---

`Smtpop` 类提供了便捷发送邮件的功能.

The `Smtpop` class provides a convenient function for sending emails.

---
- [构造函数参数](#constructor-parameters)
- [核心方法](#core-methods)
  - [连接与断开](#connection-and-disconnection)
  - [邮件操作](#mail-operations)
- [使用示例](#examples)
---

### constructor parameters
### 构造函数参数
- `host`: SMTP服务器地址 例如: "smtp.qq.com"
- `port`: SMTP服务器端口 例如: 587
- `user`: 登录用户名
- `passwd`: 授权码
- `logger`: 日志记录器

### core methods
### 核心方法
#### connection and disconnection
#### 连接与断开
1. `login()`
- 功能: 连接服务器

2. `close()`: 断开服务器
- 功能: 断开服务器

#### mail operations
#### 邮件操作
1. `add_recipient(recipient: Union[str, Iterable[str]], *args)`
- 功能: 添加收件人
- 参数:
  - `recipient`: 收件人地址
  - `*args`: `*args`也能接受单个的收件人邮箱地址或者可迭代的收件人邮箱地址容器(如列表、元组、集合)

2. `add_file(file_path)`
- 功能: 添加附件
- 参数:
  - `file_path`: 附件路径

3. `send(subject: str, body: str, html=False)`
- 功能: 发送邮件
- 参数:
  - `subject`: 邮件主题
  - `body`: 邮件正文 
  - `html`: 是否发送HTML格式的邮件

### examples
### 使用示例
```python
from hzgt.tools import Smtpop

smtpop = Smtpop(host="smtp.qq.com", port=587, user="***", passwd="***", logger=None)
smtpop.login()
smtpop.add_recipient(["***@qq.com"])
smtpop.add_file("./test.txt")
smtpop.send("测试邮件", "这是一封测试邮件")
smtpop.close()
```
