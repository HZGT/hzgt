import datetime
import os
import sys
from urllib import parse
from urllib.parse import urlparse

from ..CONST import INSTALLCMD
from ..strop import restrop
from ..fileop import getUrlFileSize, Bit_Unit_Conversion

try:
    from tqdm import tqdm
except Exception as err:
    print(err)
    os.system(INSTALLCMD("tqdm"))
    from tqdm import tqdm

try:
    import requests
except Exception as err:
    print(err)
    os.system(INSTALLCMD("requests"))
    import requests

# 屏蔽warning信息
requests.packages.urllib3.disable_warnings()


def parse_url(url_):
    _url = urlparse(url_)
    # print(_url)
    hostname = _url.hostname
    port = _url.port
    _url_port = _url.netloc
    _url_path = _url.path
    _url_name = parse.unquote(url_)  # url转码str
    _url_protocol = _url.scheme
    # print(f'域名：{hostname}\n'
    #       f'端口：{port}\n'
    #       f'域名+端口:{_url_port}\n'
    #       f'域名路径地址:{_url_path}\n'
    #       f'域名解析地址:{_url_name}\n'
    #       f'域名协议:{_url_protocol}')
    return _url_name


def UrlFileDownload(url, savepath=os.path.join("download_Files", "urldownload")):
    try:
        url_name = parse_url(url)
        url_file_size = getUrlFileSize(url)
        print('文件大小：', url_file_size)

        # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        #                         "Chrome/69.0.3497.100 Safari/537.36"}
        response = requests.get(url, stream=True)  # , headers=headers)
        response.raise_for_status()
        _endfilename = url_name.split('/')[-1]
        if _endfilename == '':
            _endfilename = url_name.split('/')[-2]
        endfilename = os.path.join(savepath, _endfilename)

        temp_size = 0
        if os.path.exists(endfilename):
            try:
                temp_size = os.path.getsize(endfilename)  # 本地已经下载的文件大小
                print(restrop(f"本地已下载 ", f=2), Bit_Unit_Conversion(temp_size))
                print(restrop(f"继续下载", f=2), Bit_Unit_Conversion(url_file_size[2] - temp_size))
            except:
                pass

        if url_file_size[2] - temp_size > 0:
            headers = {'Range': 'bytes=%d-' % temp_size}
            newr = requests.get(url, stream=True, verify=False, headers=headers)

            print(restrop(datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S'), f=3),
                  restrop('文件开始下载', f=2))

            with open(endfilename, 'ab') as file, \
                    tqdm(desc='下载中', total=url_file_size[2] - temp_size, colour='#66CDAA',
                         unit='B', unit_scale=True, unit_divisor=1024, ncols=80) as bar:
                for data in newr.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)

        print(restrop(datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S'), f=3),
              restrop('文件下载完成', f=6))

    except Exception as error:
        print(restrop(datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S'), f=3), restrop('文件下载异常'),
              f"{error}")


def downloadmain(tip_num: int, url: str, savepath=''):
    filepaths = [os.path.join(savepath, "download_Files", "urldownload"),
                 os.path.join(savepath, "download_Files", "git"),
                 os.path.join(savepath, "download_Files", "youget")]
    for fp in filepaths:
        if not os.path.isdir(fp):
            # 创建文件夹
            os.makedirs(fp)
            print("已创建文件夹", restrop(fp, f=6))

    # tip_num = int(input(f"输入代号：  {restrop('1:文件下载  2:github仓库下载  3:视频下载', f=3)}===>>>"))
    if tip_num not in [1, 2, 3]:
        exit()
    # url = input("输入文件/仓库/视频所在的url:")
    if tip_num == 1:
        UrlFileDownload(url, savepath=filepaths[0])
    elif tip_num == 2:
        print(restrop("Github仓库使用gitclone加速", f=5))
        from .gitclone import github_download
        github_download(url, savepath=filepaths[1])
        sys.exit()  # 退出程序
    elif tip_num == 3:
        from .videodownload import VideoDownload
        VideoDownload(url, savepath=filepaths[2])
        sys.exit()  # 退出程序

