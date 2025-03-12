# -*- coding: utf-8 -*-

import datetime
import os
import sys
from urllib import parse
from urllib.parse import urlparse

from ..strop import restrop
from ..fileop import get_file_size, bit_conversion
from ..Decorator import vargs

from tqdm import tqdm

import requests


def get_file_extension(url: str):
    # 解析URL
    parsed_url = urlparse(url)
    # print(parsed_url)

    # 验证URL的合法性
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError("Invalid URL")

    # 规范化路径并获取文件名
    file_path = os.path.normpath(parsed_url.path)
    file_name = os.path.basename(file_path)

    return file_name


def url_file_download(url: str, savepath=os.path.join("download_files", "urldownload")):
    # 屏蔽warning信息
    requests.packages.urllib3.disable_warnings()

    try:
        url_name = get_file_extension(url)
        url_file_size = get_file_size(url)
        print('文件大小：', url_file_size)

        response = requests.get(url, stream=True)  # , headers=headers)
        response.raise_for_status()

        endfilename = os.path.join(savepath, url_name)

        temp_size = 0
        if os.path.exists(endfilename):
            try:
                temp_size = os.path.getsize(endfilename)  # 本地已经下载的文件大小
                print(restrop(f"本地已下载 ", f=2), bit_conversion(temp_size))
                print(restrop(f"将继续下载 ", f=2), bit_conversion(url_file_size[2] - temp_size))
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


@vargs({"tip_num": {1, 2, 3}})
def downloadmain(tip_num: int, url: str, savepath: str = ""):
    """
    根据 模式tip_num 进行下载

    :param tip_num: 模式 1 文件下载 | 2 github下载 | 3 you-get下载
    :param url: url
    :param savepath: 默认保存在同目录
    :return:
    """
    savepath = os.path.abspath(savepath)
    filepaths = [os.path.join(savepath, "download_file", "urldownload"),
                 os.path.join(savepath, "download_file", "git"),
                 os.path.join(savepath, "download_file", "youget")]
    for fp in filepaths:
        if not os.path.isdir(fp):
            os.makedirs(fp)  # 创建文件夹
            print("已创建文件夹", restrop(fp, f=6))

    if tip_num not in [1, 2, 3]:
        exit()
    if tip_num == 1:
        url_file_download(url, savepath=filepaths[0])
    elif tip_num == 2:
        print(restrop("Github仓库下载加速", f=5))
        from .gitclone import github_download
        github_download(url, savepath=filepaths[1])
        exit()  # 退出程序
    elif tip_num == 3:
        from .videodownload import VideoDownload
        VideoDownload(url, savepath=filepaths[2])
        exit()  # 退出程序

