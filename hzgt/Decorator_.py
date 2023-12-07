import datetime
import time

from .strop import restrop, restrop_list

def gettime(func):
    """
    使用方法：装饰器

    在需要显示运算时间的函数前加@gettime

    :param func:
    :return: None
    """
    def get():
        start = datetime.datetime.now()
        starttime = time.time()

        print(restrop_list(["=== ",
                            "开始时间 ", start.strftime('%Y-%m-%d  %H:%M:%S'),
                            "     %s.%s()" % (func.__module__, func.__name__),
                            ],
                           [1,
                            -1, 3,
                            5,
                            ])
              )

        func()

        end = datetime.datetime.now()
        spentedtime = time.time() - starttime
        print(restrop_list(["=== ",
                            "结束时间 ", end.strftime('%Y-%m-%d  %H:%M:%S'),
                            "     总耗时 ", f"{spentedtime:.2f}", " s"
                            ],
                           [1,
                            -1, 4,
                            -1, 5, -1
                            ])
              )
    return get
