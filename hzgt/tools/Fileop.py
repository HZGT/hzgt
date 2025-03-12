import mimetypes
import os
import sys
import time
import datetime
import socket
import ssl
import html
import io
import base64
import email
import posixpath
import cgi
import urllib.parse
import http.client
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from http import HTTPStatus
import urllib
import threading
from typing import Union

from .INI import readini

import socket
from typing import Union, List


def get_ipv4_addresses() -> List[str]:
    """
    获取本机的 IPv4 地址列表
    """
    # 获取主机名
    hostname = socket.gethostname()

    # 获取 IPv4 地址列表
    ipv4_addresses = socket.gethostbyname_ex(hostname)[-1]

    # 尝试通过连接获取更多可能的 IPv4 地址
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 1))
        additional_ip = sock.getsockname()[0]
        if additional_ip not in ipv4_addresses:
            ipv4_addresses.append(additional_ip)
    except Exception:
        pass
    finally:
        sock.close()

    # 确保包含本地回环地址和默认地址
    if '127.0.0.1' not in ipv4_addresses:
        ipv4_addresses.insert(0, '127.0.0.1')
    if '0.0.0.0' not in ipv4_addresses:
        ipv4_addresses.insert(0, '0.0.0.0')

    return ipv4_addresses


def get_ipv6_addresses() -> List[str]:
    """
    获取本机的 IPv6 地址列表
    """
    # 获取主机名
    hostname = socket.gethostname()

    # 获取 IPv6 地址列表
    ipv6_addresses = []
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
        ipv6_addresses = [info[4][0] for info in addr_info]
    except socket.gaierror:
        pass

    # 尝试通过连接获取更多可能的 IPv6 地址
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        sock.connect(('2402:4e00::', 1))
        additional_ip = sock.getsockname()[0]
        if additional_ip not in ipv6_addresses:
            ipv6_addresses.append(additional_ip)
    except Exception as err:
        pass  # 不支持公网 IPV6
    finally:
        sock.close()

    return ipv6_addresses


def getip(index: int = None, ipv6: bool = False) -> Union[str, List[str]]:
    """
    获取本机 IP 地址

    :param index: 如果指定 index, 则返回 IP 地址列表中索引为 index 的 IP, 否则返回 IP 地址列表
    :param ipv6: 如果为 True, 则获取 IPv6 地址；否则获取 IPv4 地址
    :return: IP 地址 或 IP 地址列表
    """
    if index is not None and not isinstance(index, int):
        raise TypeError("参数 index 必须为整数 或为 None")

    # 获取 IPv4 或 IPv6 地址列表
    if ipv6:
        addresses = get_ipv6_addresses()
    else:
        addresses = get_ipv4_addresses()

    # 根据 index 返回结果
    if index is None:
        return addresses
    else:
        if index >= len(addresses):
            raise IndexError(f"索引超出范围, 最大索引为 {len(addresses)}")
        return addresses[index]


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
    
    function generateBoundary() {
        const characters = '0123456789abcdef';
        let boundary = '----WebKitFormBoundary';
        for (let i = 0; i < 16; i++) {
            boundary += characters[Math.floor(Math.random() * characters.length)];
        }
        return boundary;
    }
    
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('file-input');
    const uploadProgress = document.getElementById('uploadProgress');
    const fileUploadpg = document.getElementById('file-uploadpg');
    let totalSize = 0;
    let uploadedSize = 0;
    
    function submitFile() {
        var form = document.getElementById('uploadForm');
        var files = form.elements['file'].files;
        for (var i = 0; i < files.length; i++) {
            var xhr = new XMLHttpRequest();
            var rtpathdivElement = document.getElementById('rtpath');
            
            xhr.open('POST', '/upload?FileName=' + encodeURIComponent(files[i].name), true);
            const boundary = generateBoundary();
            xhr.setRequestHeader('Content-Type', 'text/html; charset=UTF-8');
            xhr.setRequestHeader('Content-Type', 'multipart/form-data; boundary=' + boundary);
            xhr.setRequestHeader('FileName', rtpathdivElement.textContent + encodeURIComponent(files[i].name));
            xhr.onload = function () {
                if (this.status === 200) {
                    alert('上传成功', this.response);
                    location.reload();
                } else {
                    alert('上传失败', this.response);
                }
            };
            xhr.upload.onprogress = function (e) {
                if (e.lengthComputable) {
                    uploadedSize = e.loaded;
                    const percent = Math.round((uploadedSize / totalSize) * 100);
                    const unit = totalSize >= 1024 * 1024?'MB' : 'KB';
                    const uploadedSizeUnit = uploadedSize >= 1024 * 1024? uploadedSize / (1024 * 1024) : uploadedSize / 1024;
                    const totalSizeUnit = totalSize >= 1024 * 1024? totalSize / (1024 * 1024) : totalSize / 1024;
                    fileUploadpg.textContent = `${percent}% [${uploadedSizeUnit.toFixed(2)}${unit}/${totalSizeUnit.toFixed(2)}${unit}]`;
                    uploadProgress.value = percent;
                }
            };
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                    } else {
                        xhr.abort();  // 取消请求
                        alert('文件发送失败, 文件过大或者网络连接错误');
                    }
                }
            };
            xhr.send(files[i]);
        }
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
        totalSize = 0;
        for (let i = 0; i < files.length; i++) {
            totalSize += files[i].size;
        }
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
                  % (urllib.parse.quote(linkname,
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


num = 0


class EnhancedHTTPRequestHandler(SimpleHTTPRequestHandler):
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

    # def do_GET(self):
    #     path = self.translate_path(self.path)
    #     if os.path.isfile(path):
    #         file_size = os.path.getsize(path)
    #
    #         fpath, filename = os.path.split(path)
    #         basename, extension = os.path.splitext(filename)
    #         self.send_response(200)
    #
    #         self.send_header("Content-Type", self.extensions_map.get(extension, "application/octet-stream") + "; charset=utf-8")
    #
    #         # 设置Content-Disposition头，使得文件被下载
    #         self.send_header("Content-Disposition", f'attachment')
    #         self.send_header("Content-Length", str(file_size))
    #
    #         self.end_headers()
    #         # 现在发送文件数据
    #         with open(path, 'rb') as file:
    #             self.wfile.write(file.read())
    #     else:
    #         super().do_GET()

    def do_POST(self):
        start_time = time.time()
        content_length = int(self.headers['Content-Length'])
        # 读取客户端发送的二进制文件数据
        file_name = urllib.parse.unquote(self.headers["FileName"])
        try:
            file_data = self.rfile.read(content_length)
        except MemoryError as err:
            self.send_error(413, "MemoryError")
            return

        with open(os.path.join(self.path, file_name), 'wb') as file:
            file.write(file_data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'File uploaded successfully.')

        end_time = time.time()
        time_elapsed_ms = int((end_time - start_time) * 1000)
        print(f"Update {file_name}[{content_length} Bytes] in {time_elapsed_ms} ms")

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
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

    # def send_head(self):
    #     path = self.translate_path(self.path)
    #     f = None
    #     if os.path.isdir(path):
    #         if not self.path.endswith('/'):
    #             self.send_response(301)
    #             self.send_header("Location", self.path + "/")
    #             self.end_headers()
    #             return None
    #         for index in "index.html", "index.htm":
    #             index = os.path.join(path, index)
    #             if os.path.exists(index):
    #                 path = index
    #                 break
    #         else:
    #             return self.list_directory(path)
    #     ctype = self.guess_type(path)
    #     if ctype.startswith('text/'):
    #         ctype += '; charset=UTF-8'
    #     try:
    #         f = open(path, 'rb')
    #     except IOError:
    #         self.send_error(404, "File not found")
    #         return None
    #     self.send_response(200)
    #     self.send_header("Content-type", ctype)
    #     fs = os.fstat(f.fileno())
    #     self.send_header("Content-Length", str(fs[6]))
    #     self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
    #     self.end_headers()
    #     return f

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
        try:
            displaypath = urllib.parse.unquote(self.path, errors='surrogatepass')
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(path)
        displaypath = html.escape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()

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
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')

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

        print(self.extensions_map.get(ext.lower()))

        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        guess, _ = mimetypes.guess_type(path)
        if guess:
            return guess
        return 'application/octet-stream'


def fix_path(_path):
    if os.name == 'nt':  # Windows系统
        if not _path.endswith('\\'):
            _path = _path + '\\'
    else:  # 类UNIX系统（Linux、Mac等）
        if not _path.endswith('/'):
            _path = _path + '/'
    return _path


def Fileserver(path: str = ".", host: str = "", port: int = 5001,
               bool_https: bool = False, certfile="cert.pem", keyfile="privkey.pem"):
    """
    快速构建文件服务器. 阻塞进程. 默认使用 HTTP

    :param path: 工作目录(共享目录路径)
    :param host: IP 默认为本地计算机的IP地址
    :param port: 端口 默认为5001
    :param bool_https: 是否启用HTTPS. 默认为False
    :param certfile: SSL证书文件路径. 默认同目录下的 cert.pem
    :param keyfile: SSL私钥文件路径. 默认同目录下的 privkey.pem
    :return: None
    """
    try:
        os.listdir(path)
    except Exception as err:
        raise err from None

    if not host:
        host = getip(-1)

    if not port:
        port = 5001

    if bool_https:
        httpd = ThreadingHTTPServer((host, port), EnhancedHTTPRequestHandler)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile, keyfile)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print(f"HTTPS service running at https://{host}:{port}")
    else:
        httpd = ThreadingTCPServer((host, port), EnhancedHTTPRequestHandler)
        print(f"HTTP service running at http://{host}:{port}")

    os.chdir(fix_path(path))  # 设置工作目录作为共享目录路径

    threading.Thread(target=httpd.serve_forever).start()
    return httpd
