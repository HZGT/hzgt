# README.md ==>> hzgt
- ### 1. 运行环境 & 函数调用
  - #### 1.1 运行环境
    - python>=3.7
  - #### 1.2 函数调用例子
    - from hzgt import *
    - from hzgt import getmidse
    - from hzgt import restrop, gettime

- ### 2. 函数使用方法
  - #### 2.1 字符串
    - ##### 2.1.1  getmidse()--2023.11.23
      >> getmidse(_string, start_string, end_string)
      > 
      > 返回 所有在start_string和end_string之间的字符串组成的列表 list[str]
      
      ```
      from hzgt import getmidse
      
      str = "12345678901234567890123456789"
      startstr = "12"
      endstr = "9"
      print(getmidse(str, startstr, endstr))

      # ['345678', '345678', '345678']
      ```

    - ##### 2.1.2  perr()--2023.11.23
      >> perr(Err: Exception, ExtraMsg: str= "", Bool_Proceed: bool=True)
      > 
      > 在try|except的except中使用 简化报错
      >
      > Bool_Proceed: 是否继续执行  [1继续执行 0退出程序]
      
      ```
      from hzgt import perr
      
      try:
          raise ValueError(1)
      except Exception as err:
          perr(err)

      # 报错-文件行数 D:\Desktop\EX\PyCharmEX\qwe.py:4
      # 报错-类型信息 'ValueError'  ValueError(1)
      ```

    - ##### 2.1.3  pic()--2023.11.23
      >> pic(*args)
      > 
      > 输出 变量名 | 变量类型 | 值
      >
      > 不建议直接使用常量，如"1, 2, 3", (1, 2, 3), [1, 2, 3]. 否则将导致变量名显示错误
      
      ```
      from hzgt import pic
      
      n = 1
      f = 1.2
      s = "str"
      l = [1, 2, 3]
      t = (1, 2, 3)
      d = {"key": "value"}
      pic(n, f, s, l, t, d)

      # Name 	|	 Type 	|	 Value
      # n    	|	 int   	|	 1
      # f    	|	 float 	|	 1.2
      # s    	|	 str   	|	 str
      # l    	|	 list  	|	 [1, 2, 3]
      # t    	|	 tuple 	|	 (1, 2, 3)
      # d    	|	 dict  	|	 {'key': 'value'}
      ```

    - ##### 2.1.4  restrop()--2023.11.23
      >> restrop(text, m='', f=1, b='')
      > 
      > 返回 颜色配置后的字符串
      > 
      > - mode 模式简记
      >  - 0---默认         
      >  - 1---高亮         
      >  - 4---下滑         
      >  - 5---闪烁         
      >  - 7---泛白         
      >  - 8---隐藏         
      >                  
      > - fore & back 颜色简记
      > 
      >  - 0---黑
      >  - 1---红
      >  - 2---绿
      >  - 3---黄
      >  - 4---蓝
      >  - 5---紫
      >  - 6---青
      >  - 7---灰
      
      ```
      from hzgt import restrop
      
      print(restrop("123"))

      # 123
      ```

    - ##### 2.1.5  restrop_list()--2023.11.23
      >> restrop_list(str_list: list[str], mfb_list: list[any])
      > 
      > 返回 字符串列表进行颜色配置后的字符串
      > 
      > ()表示不进行颜色配置
      
      ```
      from hzgt import restrop_list
      
      print(restrop_list(["123", "456", "789"],
                         [(0, 2, 0), (0, 1, 7), ()]))
      
      # 123456789
      ```

  - #### 2.2 文件大小
    - ##### 2.2.1  Bit_Unit_Conversion()--2023.11.23
      >> Bit_Unit_Conversion(fsize: int)
      > 
      > 字节单位转换 byte => KB / MB / GB 
      > 
      > 返回 (大小,单位,原大小)
      
      ```
      from hzgt import Bit_Unit_Conversion

      print(Bit_Unit_Conversion(123456780))
      
      # (117.74, 'M', 123456780)
      ```
    
    - ##### 2.2.2  getFileSize()--2023.11.23
      >> getFileSize(filepath: str)
      > 
      > 获取目录或文件的总大小
      > 
      > 返回 (大小,单位,原大小)
    
      ```
      from hzgt import getFileSize

      print(getFileSize(r"D:\Desktop\EX\PyCharmEX"))
      
      # (4.43, 'G', 4761117713)
      ```
      
    - ##### 2.2.3  getUrlFileSize()--2023.11.23
      >> getUrlFileSize(url: str)
      > 
      > 获取url上的文件的总大小
      > 
      > 返回 (大小,单位,原大小)
      
      ```
      from hzgt import getUrlFileSize

      print(getUrlFileSize("https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"))

      # (10.52, 'M', 11030264)
      ```
  - #### 2.3 装饰器
    - ##### 2.3.1 gettime()--2023.11.23
      >> gettime(func)
      > 
      > 在需要显示运算时间的函数前加@gettime
      > 
      > 最低单位秒 

      ```
      from hzgt import getUrlFileSize, gettime

      @gettime
      def main():
          print(getUrlFileSize("https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"))

      main()
      
      # ===
      # (10.52, 'M', 11030264)
      # ===开始时间 2023-11-27  01:24:26     结束时间 2023-11-27  01:24:26     总耗时 0.48 s
      ```
  - #### 2.4 下载
    - ##### 2.4.1 downloadmain()--2023.11.30
      >> downloadmain()
      > 
      > 文件/github仓库/视频 下载
      > 
      > 第一次使用将创建三个文件夹
      > 
      > 文件下载时输入代号 1. 接着输入文件下载的url. 支持断点续传
      > 
      > github仓库下载时输入代号 2. 接着输入仓库的链接. 下载时将使用gitclone加速
      > 
      > 视频下载时输入代号 3. 接着输入视频所在的url. 该下载基于you-get库
    
      ```
      from hzgt import downloadmain
      
      downloadmain()
      
      # 已创建文件夹 download_Files\urldownload
      # 已创建文件夹 download_Files\git
      # 已创建文件夹 download_Files\youget
      # 输入代号：  1:文件下载  2:github仓库下载  3:视频下载===>>>1
      # 输入url:https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip
      # 文件大小： (10.52, 'M', 11030264)
      # 2023-11-27  01:34:32 文件开始下载
      # 下载中: 100%|███████████████████████████████████████████████████████████████████████| 10.5M/10.5M [00:01<00:00, 11.1MB/s]
      # 2023-11-27  01:34:33 文件下载完成
      ```
  - #### 2.5 命令行调用显示
    - ##### 2.5.1  CmdLine()--2023.11.30
      >> CmdLine(cmd: str)
      > 
      > 执行cmd命令时可以查看输出的内容
      
      ```
      from hzgt import CmdLine
      
      cmd = "ping 192.168.1.100"
      CmdLine(cmd)
      
      # 正在 Ping 192.168.1.100 具有 32 字节的数据:
      # 来自 192.168.1.100 的回复: 字节=32 时间=116ms TTL=64
      # 来自 192.168.1.100 的回复: 字节=32 时间=341ms TTL=64
      # 来自 192.168.1.100 的回复: 字节=32 时间=356ms TTL=64
      # 来自 192.168.1.100 的回复: 字节=32 时间=374ms TTL=64
      # 
      # 192.168.1.100 的 Ping 统计信息:
      #     数据包: 已发送 = 4，已接收 = 4，丢失 = 0 (0% 丢失)，
      # 往返行程的估计时间(以毫秒为单位):
      #     最短 = 116ms，最长 = 374ms，平均 = 296ms
      ```
- ### 3. 命令行hzgt
  - #### 3.1 主函数--2023.11.30
    >> hzgt
    > 
    >> hzgt --help
    > 
    > 查看主函数的help条例

    ```
    hzgt
    
    # Usage: hzgt [OPTIONS] COMMAND [ARGS]...
    # 
    #   - d 命令行下载
    # 
    #       - m: 功能参数 1-文件下载 2-github仓库下载 3-视频下载
    # 
    #       - u: 文件/仓库/视频所在的url
    # 
    #       - s: 保存路径
    # 
    # Options:
    #   --help  Show this message and exit.
    # 
    # Commands:
    #   d  命令行 下载
    ```
  - #### 3.2 d()--2023.11.30
    >> hzgt d
    > 
    >> hzgt d -- help
    > 
    > 查看d()的help条例
 
    ```
    hzgt d    
    
    # Usage: hzgt d [OPTIONS]
    # 
    #   命令行 下载
    # 
    # Options:
    #   -m, --mode INTEGER  功能参数 1-文件下载 2-github仓库下载 3-视频下载
    #   -u, --url TEXT      文件/仓库/视频所在的url
    #   -s, --save TEXT     保存路径
    #   --help              Show this message and exit.
    ```