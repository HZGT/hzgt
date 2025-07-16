import base64
import cgi
import datetime
import email
import html
import io
import mimetypes
import os
import posixpath
import socket
import ssl
import sys
import threading
import traceback
import urllib
import urllib.parse
from email.header import Header
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingTCPServer, ThreadingMixIn

from .INI import readini
from ..core.ipss import validate_ip, getip


def _ul_li_css(_ico_base64):
    return f"""
    body {{
        background-color: #808080;
    }}
    
    .header-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 20%;
        background-color: #808080;
        display: flex;
        align-items: center;
    }}
    .fixed-title {{
        display: left;
        font-size: 14px;
        margin-left: 0;
        display: inline-block;
        vertical-align: middle;
        overflow-wrap: break-word;
        max-width: 36%;
    }}
    .form-container {{
        display: right;
        justify-content: flex-end;
        align-items: flex-start;
    }}
    
    input[type = "file"] {{
        display: inline-block;
        background-color: #c0c0c0;
        color: black;
        border: none;
        border-radius: 10%;
        padding: 0 0;
        cursor: pointer;
        max-width: 170px;
    }}
    
    .clear-input {{
        display: inline-block;
        background-color: red;
        color: black;
        border: none;
        border-radius: 5%;
        padding: 4px 8px;
        cursor: pointer;
    }}
    .clear-input:hover {{
        background-color: #218838;
        box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
    }}
    
    .upload-button {{
        background-color: #28a745;
        color: black;
        border: none;
        border-radius: 5%;
        padding: 4px 8px;
        cursor: pointer;
    }}
    .upload-button:hover {{
        background-color: #218838;
        box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
    }}
    
    :root {{
        --icon-size: 48px;
    }}
    #icon-div {{
        width: var(--icon-size);
        height: var(--icon-size);
        background-image: url('data:image/x - icon;base64,{_ico_base64}');
        /* background-size: cover;  调整背景图像大小以适应div */
        margin: 0;
        z-index: 2;
    }}
    

    ul.custom-list {{
        list-style: none;
        padding-left: 0;
    }}
    ul.custom-list li.folder::before {{
        content: "\\1F4C1"; /* Unicode 文件夹符号 */
        margin-right: 10px;
        color: blue;
        display: inline-flex;
    }}
    ul.custom-list li.file::before {{
        content: "\\1F4C4"; /* Unicode 文件符号 */
        margin-right: 10px;
        color: gray;
        display: inline-flex;
    }}

    li:hover {{
        color: #ff6900;
        background-color: #f0f000; /* 悬停时的背景色 */
        text-decoration: underline; /* 悬停时添加下划线 */
        
        animation: li_hover_animation 1s;
    }}
    @keyframes li_hover_animation {{
        from {{ background-color: #ffffff; }}
        to {{ background-color: #f0f000; }}
    }}
    
    li:active {{
        color: #0066cc;
        background-color: #c0c0c0;
    }}
    
    li {{
        flex: 1 0 auto;
        margin: 1%; /* 增加li元素之间的间距 */
        color: blue;
        background-color: #c0c0c0; /* 背景色 */
        border-style: dotted; /* 使用虚线边框，自适应长度 */
        border-color: gray;
        border-radius: 8px; /* 边框的圆角半径 */
        display: flex;
        cursor: pointer;
        z-index: 0;
    }}
    
    li a {{
        display: block;
        padding: 3px;
        text-decoration: none;
    }}
    
"""


def _ul_li_js():
    return """
    var rtpathdivElement = document.getElementById('rtpath');
    // 设置元素的style的display属性为none来隐藏div
    rtpathdivElement.style.display = 'none';
    
    const ul = document.querySelector('ul');
    const items = document.querySelectorAll('li');
    const loadThreshold = 0.5; // 当元素进入视口50%时加载
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                observer.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '0px',
        threshold: loadThreshold
    });
    
    items.forEach((item) => {
        observer.observe(item);
    });
    
    const ulcl = document.querySelector('ul.custom-list');
    ulcl.addEventListener('click', function (event) {
        const target = event.target;
        let link;
        if (target.tagName === 'LI') {
            link = target.querySelector('a');
        } else if (target.tagName === 'A') {
            link = target;
        }
        if (link) {
            link.click();
        }
    });
    
    document.addEventListener('DOMContentLoaded', function () {
        const listItems = document.querySelectorAll('ul.custom-list li');
        listItems.forEach((item) => {
            const text = item.textContent.trim();
            if (text.endsWith('/')) {
                item.classList.add('folder');
            } else {
                item.classList.add('file');
            }
        });
    });
    
    document.addEventListener('DOMContentLoaded', function () {
        const h1Element = document.querySelector('div.header-container');
        const h1Height = h1Element.offsetHeight;
        const ulElement = document.querySelector('ul.custom-list');
        ulElement.style.marginTop = `${h1Height + 20}px`;
    });
    
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('uploadProgress');
    const fileUploadpg = document.getElementById('file-uploadpg');
    let totalSize = 0;
    let uploadedSizes = []; // 存储每个文件的上传进度
    let completedCount = 0; // 完成上传的文件数
    
    function formatSize(size) {
        return size >= 1024 * 1024 
            ? `${(size / (1024 * 1024)).toFixed(2)}MB` 
            : `${(size / 1024).toFixed(2)}KB`;
    }
    
    function updateProgress() {
        const totalUploaded = uploadedSizes.reduce((acc, cur) => acc + cur, 0);
        const percent = Math.min(100, (totalUploaded / totalSize * 100).toFixed(2));
        const totalSizeFormatted = formatSize(totalSize);
        const uploadedFormatted = formatSize(totalUploaded);
        
        fileUploadpg.textContent = `${percent}% [${uploadedFormatted}/${totalSizeFormatted}]`;
        uploadProgress.value = percent;
    }

    function submitFile() {
        const files = fileInput.files;
        completedCount = 0;
        uploadedSizes = new Array(files.length).fill(0);
        
        Array.from(files).forEach((file, index) => {
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            const path = document.getElementById('rtpath').textContent;
    
            formData.append('file', file);
            formData.append('filename', path + file.name);
    
            xhr.upload.onprogress = e => {
                if (e.lengthComputable) {
                    uploadedSizes[index] = e.loaded;
                    updateProgress();
                }
            };
    
            xhr.onload = () => {
                completedCount++;
                if (completedCount === files.length) {
                    if (xhr.status === 200) {
                        // 所有文件完成后更新最终状态
                        uploadedSizes[index] = file.size;
                        updateProgress();
                        setTimeout(() => {
                            alert("所有文件上传成功");
                            location.reload();
                        }, 500);
                    } else {
                        alert(`文件 ${file.name} 上传失败`);
                    }
                }
            };
    
            xhr.onerror = () => {
                alert(`文件 ${file.name} 上传失败`);
                uploadedSizes[index] = 0; // 失败时重置进度
            };
    
            xhr.open('POST', window.location.pathname + 'upload');
            xhr.send(formData);
        });
    
        return false;
    }

    const clearButton = document.getElementById('clearselected');
    clearButton.addEventListener('click', function () {
        location.reload();
    });
    
    document.getElementById('uploadForm').addEventListener('submit', function (e) {
        e.preventDefault();
        submitFile();
    });
    
    let timer;
    // 设置初始的定时器
    timer = setTimeout(function () {
        location.reload();
    }, 60000);
    
    fileInput.addEventListener('click', function () {
        // 清除定时器
        clearTimeout(timer);
    });
    fileInput.addEventListener('change', function () {
        const files = this.files;
        totalSize = Array.from(files).reduce((acc, file) => acc + file.size, 0);
        uploadProgress.value = 0;
        fileUploadpg.textContent = '0% [0.00KB/0.00KB]';
        // 清除定时器
        clearTimeout(timer);
    });
    fileInput.addEventListener('input', function () {
        // 清除定时器
        clearTimeout(timer);
    });
    """


def _list2ul_li(titlepath: str, _path: str, pathlist: list):
    """
    将列表转换为lu的li样式
    :return:
    """
    _r = []
    parts = titlepath.split('/')
    result = []
    current_path = ''
    for part in parts:  # 处理标题样式
        if part:
            current_path += '/' + part
            link = f"<a href='{current_path}' style='color: #40E0D0;'>{part}</a>"
            result.append(link)

    common_part = "<a href='/' style='color: #40E0D0;'>...</a>/"
    if result:
        end_title = common_part + '/'.join(result) + "/"
    else:
        end_title = common_part

    for name in pathlist:  # 处理文件夹和文件li
        fullname = os.path.join(_path, name)
        displayname = linkname = name
        if os.path.isdir(fullname):
            displayname = name + '/'
            linkname = name + '/'
        if os.path.islink(fullname):
            displayname = name + "@"
        _r.append("<li><a href='%s' style='color: #000080;'>%s</a></li>"
                  % (urllib.parse.quote(linkname, encoding='utf-8',
                                        errors='surrogatepass'),
                     html.escape(displayname, quote=False)))
    return f"""
    <div id="rtpath">{_path}</div>
    <div class="header-container">
        <div id="icon-div"></div>
        <div class="fixed-title">
            HZGT文件服务器
            <br>
            当前路径: {end_title}
        </div>
        <div class="form-container">
            <form id="uploadForm" action="/upload" enctype="multipart/form-data" method="post">
                <div>
                    <input type="file" name="file" multiple id="file-input">
                </div>
                <div>
                    <input type="submit" value="上传文件", class="upload-button">
                    <span id="file-uploadpg">0%</span>
                </div>
                <progress id="uploadProgress" value="0" max="100"></progress>
            </form>
            <div>
                <input type="submit" value="清除选择" class=“clear-input” id="clearselected">
            </div>
        </div>
    </div>""", _r


def _convert_favicon_to_base64():
    with open(os.path.join(os.path.dirname(__file__), 'favicon.ico'), 'rb') as f:
        data = f.read()
        b64_data = base64.b64encode(data).decode('utf-8')
    return b64_data


class __EnhancedHTTPRequestHandler(SimpleHTTPRequestHandler):
    @staticmethod
    def get_default_extensions_map():
        """
        返回提供文件的默认 MIME 类型映射
        """

        extensions_map = readini(os.path.join(os.path.dirname(__file__), "extensions_map.ini"))["default"]
        # 不能直接用相对路径, 不然经过多脚本接连调用后会报错
        # FileNotFoundError: [Errno 2] No such file or directory: 'extensions_map.ini'

        return extensions_map

    def __init__(self, *args, **kwargs):
        self.extensions_map = self.get_default_extensions_map()
        super().__init__(*args, **kwargs)

    def do_POST(self):
        try:
            # 确保Content-Type存在且正确
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Invalid Content-Type")
                return

            # 完整环境变量设置
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': self.headers.get('Content-Length', 0)
            }

            # 解析FormData
            form_data = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
                keep_blank_values=True
            )

            # 获取文件字段和路径 ✅ 正确获取方式
            if 'file' not in form_data or 'filename' not in form_data:
                self.send_error(400, "Missing required fields")
                return

            file_item = form_data['file']  # 获取FieldStorage对象
            filename = form_data.getvalue('filename', '')

            # 安全处理路径和文件名
            safe_filename = os.path.basename(filename)
            # 构建完整保存路径 ✅
            # 获取当前请求路径（去除末尾的upload）
            current_dir = self.path
            if current_dir.endswith('upload'):
                current_dir = current_dir[:-6]
            base_path = self.translate_path(current_dir)
            # 确保目录存在
            os.makedirs(base_path, exist_ok=True)
            save_path = os.path.join(base_path, safe_filename)
            # print(self.path, base_path, self.translate_path(self.path), save_path)

            # 写入文件（分块读取避免内存溢出）
            if hasattr(file_item, 'file'):  # 检查是否为文件对象
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = file_item.file.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            else:  # 处理小文件直接存储在内存中的情况
                with open(save_path, 'wb') as f:
                    f.write(file_item.value)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f'成功上传文件: {safe_filename}'.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"服务器错误: {str(e)}")
            print(f"上传错误: {traceback.format_exc()}")

    def send_head(self):
        path = self.translate_path(self.path)
        # print(self.path, path)

        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.isfile(index):
                    path = index
                    break
            else:
                return self.list_directory(path)

        # 文件下载处理
        if os.path.isfile(path):
            try:

                f = open(path, 'rb')
                fs = os.fstat(f.fileno())

                self.send_response(200)
                self.send_header("Content-Type", self.guess_type(path))
                filename = os.path.basename(path)
                try:
                    # RFC 5987编码处理
                    encoded_filename = Header(filename, 'utf-8').encode()
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{encoded_filename}"')
                except UnicodeEncodeError:
                    # 兼容性处理
                    self.send_header("Content-Disposition",
                                     "attachment; filename*=UTF-8''{}".format(
                                         urllib.parse.quote(filename, safe='')))
                self.send_header("Content-Length", str(fs.st_size))
                self.send_header("Last-Modified",
                                 self.date_time_string(fs.st_mtime))
                self.end_headers()
                return f
            except OSError as e:
                self.send_error(404, "File not found")
            except Exception as e:
                self.send_error(500, str(e))

        ctype = self.guess_type(path)
        # check for trailing "/" which should return 404. See Issue17324
        # The test for this was added in test_httpserver.py
        # However, some OS platforms accept a trailingSlash as a filename
        # See discussion on python-dev and Issue34711 regarding
        # parsing and rejection of filenames with a trailing slash
        if path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            try:
                f = open(path, 'rb', encoding='utf-8')
            except:
                f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            # Use browser cache if possible
            if ("If-Modified-Since" in self.headers
                    and "If-None-Match" not in self.headers):
                # compare If-Modified-Since and time of last file modification
                try:
                    ims = email.utils.parsedate_to_datetime(
                        self.headers["If-Modified-Since"])
                except (TypeError, IndexError, OverflowError, ValueError):
                    # ignore ill-formed values
                    pass
                else:
                    if ims.tzinfo is None:
                        # obsolete format with no timezone, cf.
                        # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    if ims.tzinfo is datetime.timezone.utc:
                        # compare to UTC datetime of last modification
                        last_modif = datetime.datetime.fromtimestamp(
                            fs.st_mtime, datetime.timezone.utc)
                        # remove microseconds, like in If-Modified-Since
                        last_modif = last_modif.replace(microsecond=0)

                        if last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.end_headers()
                            f.close()
                            return None

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified",
                             self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise

    def list_directory(self, path):
        try:
            _list = os.listdir(path)
        except PermissionError as err:
            self.send_error(
                HTTPStatus.FORBIDDEN,
                ''.join([c for c in f"{type(err).__name__}: {err}" if ord(c) < 128]))
            return None
        except OSError as err:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                ''.join([c for c in f"{type(err).__name__}: {err}" if ord(c) < 128]))
            return None
        except Exception as err:
            self.send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                ''.join([c for c in f"{type(err).__name__}: {err}" if ord(c) < 128]))
            return None
        _list.sort(key=lambda a: a.lower())
        r = []
        # 强制使用UTF-8编码生成响应
        enc = 'utf-8'
        r.append(f'<meta charset="{enc}">')
        r.append(f'<meta http-equiv="Content-Type" content="text/html; charset={enc}">')

        # 路径显示处理
        try:
            displaypath = urllib.parse.unquote(self.path, encoding=enc, errors='replace')
        except:
            displaypath = urllib.parse.unquote(self.path)

        # enc = sys.getfilesystemencoding()

        ico_base64 = _convert_favicon_to_base64()
        title, li_list = _list2ul_li(displaypath, path, _list)  # 显示在浏览器窗口

        r.append('<!DOCTYPE HTML>')
        r.append('<html lang="zh">')
        r.append('<head>')
        r.append(f'<meta charset="{enc}">\n<title>HZGT 文件服务器 {displaypath}</title>\n')  # 显示在浏览器标题栏
        r.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        r.append(f'''<link rel="icon" href="data:image/x-icon;base64,{ico_base64}" type="image/x-icon">''')
        r.append('<style>')
        r.append(_ul_li_css(ico_base64))
        r.append('</style>')

        r.append(f'</head>')
        r.append(f'<body>\n')

        r.append(title)  # 标题
        r.append('<hr>\n<ul class="custom-list">')
        for _li in li_list:
            r.append(_li)
        r.append('</ul>\n<hr>\n')

        r.append("<script>")
        r.append(_ul_li_js())
        r.append("</script>")

        r.append('</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'replace')  # 使用错误替换策略

        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def guess_type(self, path):
        """Guess the type of a file.

                Argument is a PATH (a filename).

                Return value is a string of the form type/subtype,
                usable for a MIME Content-type header.

                The default implementation looks the file's extension
                up in the table self.extensions_map, using application/octet-stream
                as a default; however it would be permissible (if
                slow) to look inside the data to make a better guess.

                """
        base, ext = posixpath.splitext(path)

        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        guess, _ = mimetypes.guess_type(path)
        if guess:
            return guess
        return 'application/octet-stream'


def __fix_path(_path):
    if os.name == 'nt':  # Windows系统
        if not _path.endswith('\\'):
            _path = _path + '\\'
    else:  # 类UNIX系统（Linux、Mac等）
        if not _path.endswith('/'):
            _path = _path + '/'
    return _path


def Fileserver(path: str = ".", host: str = "::", port: int = 5001,
               bool_https: bool = False, certfile="cert.pem", keyfile="privkey.pem"):
    """
    快速构建文件服务器. 阻塞进程. 默认使用 HTTP

    >>> from hzgt.tools import Fileserver as fs

    >>> fs()  # 在当前目录启动文件服务器

    :param path: 工作目录(共享目录路径)
    :param host: IP 默认为本地计算机的IP地址 默认为 "::"
    :param port: 端口 默认为5001
    :param bool_https: 是否启用HTTPS. 默认为False
    :param certfile: SSL证书文件路径. 默认同目录下的 cert.pem
    :param keyfile: SSL私钥文件路径. 默认同目录下的 privkey.pem
    :return: None
    """
    path = __fix_path(path)
    # 路径预处理：兼容Unicode路径
    try:
        # 显式转换为Unicode路径
        path = os.path.abspath(path).encode('utf-8').decode(sys.getfilesystemencoding())
    except UnicodeEncodeError:
        path = os.path.abspath(path)

    try:
        os.listdir(path)
    except Exception as err:
        raise ValueError(f"无效的共享目录路径: {path}") from err

    # 端口默认值设置
    port = port or 5001
    host = host or "::"

    td = validate_ip(host)  # 校验并标准化IP地址
    if td["valid"]:
        host = td["normalized"]
        bool_ipv6 = True if td["type"] == "IPv6" else False
    else:
        raise ValueError(f"无效的IP地址: {host}")

    # 服务器类（支持双栈）
    class DualStackServer(ThreadingMixIn, HTTPServer):
        address_family = socket.AF_INET6 if bool_ipv6 else socket.AF_INET

        def server_bind(self):
            # 启用地址重用
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 如果是IPv6，启用双栈支持
            if bool_ipv6:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            super().server_bind()

    # 创建服务器实例
    server_address = (host, port)

    try:
        httpd = DualStackServer(server_address, __EnhancedHTTPRequestHandler)
    except Exception as e:
        if "Address family not supported" in str(e) and bool_ipv6:
            # IPv6失败时回退到IPv4
            print("IPv6不可用，使用IPv4")
            httpd = ThreadingTCPServer(server_address, __EnhancedHTTPRequestHandler)
        else:
            raise e from None

    # HTTPS处理
    protocol = "http"
    if bool_https:
        protocol = "https"
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile, keyfile)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    if host != "::":
        print(f"{protocol.upper()} service running at {protocol}://"
              f"{f'[{host}]' if bool_ipv6 else host}:{port}")
    else:
        print(f"{protocol.upper()} service running at")
        for i in getip():
            ipinfo = validate_ip(i)
            norip = ipinfo["normalized"]
            print(f"{protocol}://{f'[{norip}]' if ipinfo['type'] == 'IPv6' else norip}:{port}")

    os.chdir(path)  # 设置工作目录作为共享目录路径

    httpd.max_buffer_size = 1024 * 1024 * 100  # 100MB缓冲区

    threading.Thread(target=httpd.serve_forever).start()
    return httpd
