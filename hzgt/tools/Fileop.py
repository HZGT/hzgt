import base64
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
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingTCPServer, ThreadingMixIn

from multipart import parse_form

from .INI import readini
from ..core.ipss import getip, get_server_urls, AddressFamily


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
        margin: 1%;
        color: blue;
        background-color: #c0c0c0;
        border-style: dotted;
        border-color: gray;
        border-radius: 8px;
        display: flex;
        align-items: center;          /* 垂直居中 */
        padding: 6px 12px;
        gap: 10px;
        flex-wrap: nowrap;
        /* 去掉 justify-content，默认为 flex-start，使 a 靠左 */
    }}

    li a {{
        display: inline-block;        /* 保持内联，不独占一行 */
        padding: 3px;
        text-decoration: none;
        font-size: 15px;
        color: #000080;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 60%;              /* 防止文件名过长 */
        flex-shrink: 1;
    }}

    /* 文件信息（大小 + 修改时间），靠右显示 */
    .file-info {{
        font-size: 13px;
        color: #333;
        display: flex;
        gap: 15px;
        flex-shrink: 0;
        align-items: center;
        white-space: nowrap;
        margin-left: auto;           /* 自动靠右 */
    }}

    /* 保留悬停和点击效果 */
    li:hover {{
        color: #ff6900;
        background-color: #f0f000;
        text-decoration: underline;
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
    _r = []
    parts = titlepath.split('/')
    result = []
    current_path = ''
    for part in parts:
        if part:
            current_path += '/' + part
            link = f"<a href='{current_path}' style='color: #40E0D0;'>{part}</a>"
            result.append(link)

    common_part = "<a href='/' style='color: #40E0D0;'>...</a>/"
    if result:
        end_title = common_part + '/'.join(result) + "/"
    else:
        end_title = common_part

    for name in pathlist:
        fullname = os.path.join(_path, name)
        displayname = linkname = name
        is_dir = os.path.isdir(fullname)
        is_link = os.path.islink(fullname)

        if is_dir:
            displayname = name + '/'
            linkname = name + '/'
        if is_link:
            displayname = name + "@"

        # 获取文件信息
        try:
            stat = os.stat(fullname)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            if is_dir:
                size_str = "文件夹"
            else:
                size_bytes = stat.st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        except Exception:
            mtime = "未知"
            size_str = "未知"

        link_href = urllib.parse.quote(linkname, encoding='utf-8', errors='surrogatepass')
        link_text = html.escape(displayname, quote=False)

        # ✅ 关键修改：根据 is_dir 设置 li 的 class
        li_class = "folder" if is_dir else "file"
        item_html = f"""
        <li class="{li_class}">
            <a href="{link_href}">{link_text}</a>
            <div class="file-info">
                <span>大小: {size_str}</span>
                <span>修改: {mtime}</span>
            </div>
        </li>
        """
        _r.append(item_html)

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
                    <input type="submit" value="上传文件" class="upload-button">
                    <span id="file-uploadpg">0%</span>
                </div>
                <progress id="uploadProgress" value="0" max="100"></progress>
            </form>
            <div>
                <input type="submit" value="清除选择" class="clear-input" id="clearselected">
            </div>
        </div>
    </div>""", _r


def _convert_favicon_to_base64():
    with open(os.path.join(os.path.dirname(__file__), 'favicon.ico'), 'rb') as f:
        data = f.read()
        b64_data = base64.b64encode(data).decode('utf-8')
    return b64_data


# 1. 定义回调类来收集解析的数据
class _FormDataCollector:
    def __init__(self):
        self.values = {}
        self.files = {}

    def on_field(self, name, value):
        # 处理普通表单字段，name 和 value 通常是 bytes 或 str
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        self.values[name] = value

    def on_file(self, name, file_object):
        # 处理文件字段，name 通常是 bytes 或 str，file_object 包含文件数据
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        self.files[name] = file_object

    def on_end(self):
        pass


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

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except ConnectionError:
            # 客户端提前断开连接，直接忽略，不打印任何错误
            self.close_connection = True
        except Exception as e:
            # 其他未预期的错误可选择性记录日志（也可忽略）
            self.log_error("Request handling error: %s", traceback.format_exc())
            self.close_connection = True

    def do_POST(self):
        try:
            # ---------- 1. 检查 Content-Type ----------
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Invalid Content-Type")
                return

            # ---------- 2. 准备变量 ----------
            # 用于存储普通字段（如 filename）
            form_fields = {}
            # 用于传递文件保存路径（在回调中设置）
            save_path = None

            # ---------- 3. 定义字段回调 ----------
            def on_field(field):
                # field.field_name 是 bytes，field.value 也是 bytes
                name = field.field_name.decode('utf-8')
                value = field.value.decode('utf-8')
                form_fields[name] = value

            # ---------- 4. 定义文件回调（流式写入，不占用大量内存） ----------
            def on_file(file_obj):
                nonlocal save_path  # 声明 nonlocal

                # 获取原始文件名（bytes -> str）
                raw_filename = file_obj.file_name.decode('utf-8') if file_obj.file_name else 'unnamed'

                # 如果表单中有 'filename' 字段，则使用它作为保存名，否则用原始文件名
                save_name = form_fields.get('filename', raw_filename)
                safe_filename = os.path.basename(save_name)  # 安全处理，防止路径遍历

                # 构建保存目录
                # 根据请求路径决定保存位置：如果路径以 '/upload' 结尾，则去除
                current_dir = self.path
                if current_dir.endswith('/upload'):
                    current_dir = current_dir[:-7]  # 去掉 '/upload'
                elif current_dir.endswith('upload'):
                    current_dir = current_dir[:-6]  # 去掉 'upload'
                base_path = self.translate_path(current_dir)
                os.makedirs(base_path, exist_ok=True)

                # 最终完整路径
                full_path = os.path.join(base_path, safe_filename)
                save_path = full_path  # 保存到外部变量，供后续使用

                # 从 file_obj.file_object 读取并流式写入磁盘
                # file_obj.file_object 是类文件对象（如 BytesIO 或临时文件）
                file_obj.file_object.seek(0)  # 确保从开头读
                with open(full_path, 'wb') as f:
                    while True:
                        chunk = file_obj.file_object.read(8192)  # 8KB 块
                        if not chunk:
                            break
                        f.write(chunk)

            # ---------- 5. 调用解析函数 ----------
            parse_form(self.headers, self.rfile, on_field, on_file)

            # ---------- 6. 检查是否成功接收到文件 ----------
            if save_path is None:
                self.send_error(400, "No file uploaded")
                return

            # ---------- 7. 返回成功响应 ----------
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            # 成功消息
            self.wfile.write(f'成功上传文件: {os.path.basename(save_path)}'.encode('utf-8'))

        except Exception as e:
            # ---------- 8. 异常处理（避免编码错误） ----------
            print(f"上传错误: {traceback.format_exc()}")
            # 发送简单的英文错误，避免 UnicodeEncodeError
            self.send_error(500, "Internal Server Error")

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
                # 生成兼容 ASCII 的备选文件名（移除所有非 ASCII 字符）
                ascii_name = filename.encode('ascii', 'ignore').decode('ascii')
                # 对原始文件名进行百分号编码，用于 filename* 参数
                encoded_filename = urllib.parse.quote(filename, safe='')
                # 同时设置 filename（后备）和 filename*（推荐）
                disposition = f"attachment; filename=\"{ascii_name}\"; filename*=utf-8''{encoded_filename}"
                self.send_header("Content-Disposition", disposition)

                self.send_header("Content-Length", str(fs.st_size))
                self.send_header("Last-Modified",
                                 self.date_time_string(int(fs.st_mtime)))
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
                             self.date_time_string(int(fs.st_mtime)))
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
        """Guess the type of file.

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


def file_server(path: str = ".", host: str = None, port: int = 5001,
                bool_run: bool = True,
                bool_https: bool = False, certfile="cert.pem", keyfile="privkey.pem"):
    """
    快速构建文件服务器，返回配置好的 HTTP 服务器实例。

    调用后需要自行启动服务器(bool_run为False的情况下)：
      - 阻塞方式：`httpd.serve_forever()`
      - 非阻塞方式（多线程）：`threading.Thread(target=httpd.serve_forever, daemon=True).start()`

    默认使用 HTTP。

    >>> from hzgt.tools import file_server as fs
    >>> httpserver, server_urls = fs(bool_run=False)        # 在当前目录创建服务器（不启动）
    >>> httpserver.serve_forever()             # 启动（阻塞）

    # 多线程方式启动

    >>> import threading
    >>> from hzgt.tools import file_server as fs
    >>> httpserver, server_urls = fs(bool_run=False)        # 在当前目录创建服务器（不启动）
    >>> threading.Thread(target=httpserver.serve_forever, daemon=True).start()

    :param path: 工作目录(共享目录路径)
    :param host: IP 默认为本地计算机的IPv4地址 (通过 getip 获取)
    :param port: 端口 默认为5001
    :param bool_run: 是否在函数内直接启动服务器
    :param bool_https: 是否启用HTTPS. 默认为False
    :param certfile: SSL证书文件路径. 默认同目录下的 cert.pem
    :param keyfile: SSL私钥文件路径. 默认同目录下的 privkey.pem
    :return: HTTP服务器实例, 生成的url列表
    """
    # 确定主机地址
    host = host or getip(-1, family=AddressFamily.IPV4, ignore_link_local=True)

    port = port or 5001
    path = __fix_path(path)

    # 路径预处理：兼容Unicode路径
    try:
        path = os.path.abspath(path).encode('utf-8').decode(sys.getfilesystemencoding())
    except UnicodeEncodeError:
        path = os.path.abspath(path)

    try:
        os.listdir(path)
    except Exception as err:
        raise ValueError(f"无效的共享目录路径: {path}") from err

    is_ipv6_wildcard = host == "::"

    # 服务器类（支持双栈，仅对 "::" 启用双栈模式）
    class DualStackServer(ThreadingMixIn, HTTPServer):
        address_family = socket.AF_INET6 if is_ipv6_wildcard else socket.AF_INET

        def server_bind(self):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if is_ipv6_wildcard:
                # 启用 IPv6 双栈，允许同时处理 IPv4 连接
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            super().server_bind()

    server_address = (host, port)

    try:
        httpd = DualStackServer(server_address, __EnhancedHTTPRequestHandler)
    except Exception as e:
        if "Address family not supported" in str(e) and is_ipv6_wildcard:
            # IPv6 不可用时回退到 IPv4
            httpd = ThreadingTCPServer(server_address, __EnhancedHTTPRequestHandler)
        else:
            raise e from None

    # HTTPS 配置
    protocol = "http"
    if bool_https:
        protocol = "https"
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile, keyfile)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        except Exception as e:
            raise RuntimeError(f"无法启用 HTTPS，请检查证书文件：{e}") from e

    os.chdir(path)  # 设置工作目录作为共享目录路径
    httpd.max_buffer_size = 1024 * 1024 * 100  # 100MB 缓冲区

    # 生成并打印可访问的 URL 列表
    urls = get_server_urls(host=host, port=port, protocol=protocol, include_ipv4=True)

    if urls:
        print(f"{protocol.upper()} 服务可通过以下地址访问：")
        for url in urls:
            print(f"  {url}")
    else:
        print("未找到可访问的地址，请检查网络配置。")

    if bool_run:

        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, urls
