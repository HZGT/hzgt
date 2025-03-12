# -*- coding: utf-8 -*-

import os
import subprocess
import time

from ..strop import restrop

def VideoDownload(url, savepath=os.path.join("download_file", "youget")):
    import you_get

    current_path = os.path.join(os.getcwd(), savepath)
    cmd = f'you-get "{url}" -o "{current_path}"'
    print("cmd命令：", restrop(cmd, f=5))
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


if __name__ == "__main__":
    url = input('输入视频url地址：')
    VideoDownload(url)
