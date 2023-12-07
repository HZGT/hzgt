import os
import subprocess

from ..strop import restrop


def github_download(path, savepath=os.path.join("download_Files", "git")):
    currentpath = os.getcwd()  # 获取脚本绝对路径
    newpath = 'https://gitclone.com' + path[7:]

    if path.split("/")[-1] != '':
        filepath = path.split("/")[-1]  # 保存路径
    else:
        filepath = path.split("/")[-2]  # 保存路径

    outpath = os.path.join(currentpath, savepath, filepath)

    print(restrop('GitHub源地址：'), path, restrop('\n镜像地址：'), newpath, restrop('\n本地存储地址：'), outpath)

    cmd = f'git clone {newpath} {outpath}'
    # cmd = f'git clone {outpath}'
    print('cmd命令：', cmd)
    print('正在clone...请勿关闭程序...')

    Running_Bool = True
    Running_Time = 1
    while Running_Bool:
        a = subprocess.getoutput(cmd)
        print(a)
        if "You appear to have cloned an empty repository" in a:
            Running_Time += 1
            print(restrop(f"正在尝试 - 第 {Running_Time} 次", f=3))
            if Running_Time >= 3:
                break
        else:
            break


if __name__ == "__main__":
    url = input('输入GitHub仓库地址：')
    github_download(url)
