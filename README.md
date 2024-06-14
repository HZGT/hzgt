# [目录](#正文)
- ### 1. 运行环境 & 函数调用
- ### [2. func](#2.-func)
  - #### [2.0 查看函数帮助](####2.0-查看函数帮助)
    - ##### 2.6.4 Class_Register--2024.04.21
- ### [3.cmdline](#cmdline)
- ### cmdline

# 正文
- ### 1. 运行环境 & 函数调用
  - #### 1.1 运行环境
    - python>=3.8
    - 建议版本[Suggested version] : python == 3.11
  - #### 1.2 调用例子
    ```python
    from hzgt import *
    from hzgt import gettime
    from hzgt import restrop, Ftpclient
    ```

<a name="2. func"></a>
- ### 2. func
  - #### 2.0 查看函数帮助
    ```python
    import hzgt
    from hzgt import *
    
    help(hzgt)
    help(hzgt.Mysqldbop)
    ``` 
  - #### 2.1 字符串
    - ##### 2.1.1 getmidse()--2023.11.23
    - ##### 2.1.2 pic()--2023.11.23
    - ##### 2.1.3 restrop()--2023.11.23
    - ##### 2.1.4 restrop_list()--2023.11.23
  - #### 2.2 文件
    - ##### 2.2.1 bit_unit_conversion()--2023.11.23
    - ##### 2.2.2 get_dir_size()--2023.11.23
    - ##### 2.2.3 get_urlfile_size()--2023.11.23
  - #### 2.3 装饰器
    - ##### 2.3.1 gettime()--2023.11.23
    - ##### 2.3.2 timelog()--2024.06.13
  - #### 2.4 下载
    - ##### 2.4.1 downloadmain()--2023.11.30
  - #### 2.5 命令行调用显示
    - ##### 2.5.1 
  - #### 2.6 tools
    - ##### 2.6.1 Mqttop--2024.02.01
    - ##### 2.6.2 Mysqldbop--2024.02.01
    - ##### 2.6.3 Func_Register--2024.04.21
    ```python
    """
    函数注册器
    """
    from hzgt import Func_Register
    my_register = Func_Register()
    
    @my_register
    def add(a, b):
        return a + b
    
    @my_register
    def multiply(a, b):
        return a * b
    
    @my_register('matrix multiply')
    def mul_multiply(a, b):
        pass
    
    @my_register
    def minus(a, b):
        return a - b
    
    @my_register
    def custom_op(a, b):
        return a * b + a + b
    
    if __name__ == '__main__':
        # check register information
        for k, v in my_register.items():
            print(f"key: {k}, value: {v}")
        print()
    
        # math open
        num1, num2 = 1, 2
        for func_name, func in my_register.items():
            print(f"{func_name} for {num1} and {num2}: ", func(num1, num2))
    
    
    # OUTPUT: 
    
    # key: add, value: <function add at 0x104777d90>
    # key: multiply, value: <function multiply at 0x104939d80>
    # key: matrix multiply, value: <function mul_multiply at 0x10493a440>
    # key: minus, value: <function minus at 0x10493a3b0>
    # key: custom_op, value: <function custom_op at 0x104939cf0>
    # 
    # add for 1 and 2:  3
    # multiply for 1 and 2:  2
    # matrix multiply for 1 and 2:  None
    # minus for 1 and 2:  -1
    # custom_op for 1 and 2:  5
    ```
    - ##### 2.6.4 Class_Register--2024.04.21
    ```python
    """
    类注册器
    """
    from hzgt import Class_Register

    class Registers:
        model = Class_Register('model')
        dataset = Class_Register('dataset')

    class Model:
        pass

    @Registers.model
    class Model1(Model):
        pass

    @Registers.model
    class Model2(Model):
        pass

    @Registers.model
    class Model3(Model):
        pass

    @Registers.dataset
    class Dataset1:
        pass

    print(Registers.model.items())
    print(Registers.dataset.items())
    
    
    # OUTPUT: 
    
    # dict_items([('Model1', <class '__main__.Model1'>), ('Model2', <class '__main__.Model2'>), ('Model3', <class '__main__.Model3'>)])
    # dict_items([('Dataset1', <class '__main__.Dataset1'>)])
    ```
    - ##### 2.6.4 FTP--2024.06.05
    ```python
    # [class] Ftpserver
    ```
    ```python
    # [class] Ftpclient
    ```
    - ##### 2.6.5 INI--2024.06.12

    > 该部分基于 python库ini-parser[版本1.2.1 / MIT许可] 修改 
    > 
    > This part is modified based on the python library ini-parser [version 1.2.1 / MIT license].
    > 
    > 详细内容可见: [ini-parser](https://pypi.org/project/ini-parser/)
    > 
    > Details are available here: [ini-parser](https://pypi.org/project/ini-parser/)
    ```python
    # [func] readini()
    ```
    ```python
    # [func] saveini()
    ```
<a name="cmdline"></a>
- ### 3.cmdline
  - #### 3.1 d()--2023.11.30