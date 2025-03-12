# -*- coding: utf-8 -*-

import os
import subprocess

from ..strop import restrop


def github_download(path, savepath=os.path.join("download_file", "git")):
    newpath = 'https://gitclone.com' + path[7:]

    if path.split("/")[-1] != '':
        filepath = path.split("/")[-1]  # 保存路径
    else:
        filepath = path.split("/")[-2]  # 保存路径

    outpath = os.path.join(os.getcwd(), savepath, filepath)

    print(restrop('GitHub源地址：'), path, restrop('\n镜像地址：'), newpath, restrop('\n本地存储地址：'), outpath)

    cmd = f'git clone {newpath} {outpath}'
    # cmd = f'git clone {outpath}'
    print('cmd命令：', cmd)
    print('正在clone...请勿关闭程序...')

    a = subprocess.getoutput(cmd)
    print(a)
