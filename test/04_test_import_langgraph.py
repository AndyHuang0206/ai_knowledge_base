from app.process.import_.agent.main_graph import import_graph_app
from app.process.import_.agent.state import create_default_state,ImportGraphState
from app.shared.runtime.logger import  logger
import json

"""
  json python数据 == json字符串互相转换! 
     json.dump / dumps  [倾倒]  python的数据转成json相关的数据 [向外] dump转到外部的文件[备份] dumps转成json字符串[可视化]
                s str 
     json.load / loads  [加载]  把json的数据转成python的数据   [向内] load将外部json文件[还原] loads将json字符串转成python[模型的返回值处理]
     dumps(参数1=要转成jsonpython对象,indent=4层次之间带有4个缩进,ensure_ascii=False 中文转成ascii编码! 我爱你中国 = %xx)
"""

# 动态测试 [graph  stream | invoke ]  我们没有编写业务! 看图的设计结构!  适合: 完成业务开发的测试
# 创建一个对应的state  task_id = 任务标识  local_file_path = 解析文件地址
state:ImportGraphState = create_default_state(task_id="007",local_file_path="xxx.md")
logger.info(f"开始进行动态执行测试,测试参数: \n {json.dumps(state,indent=4,ensure_ascii=False)}")
result_state = import_graph_app.invoke(input=state)
logger.info(f"完成动态执行测试,测试结果: \n {json.dumps(result_state,indent=4,ensure_ascii=False)}")

# 静态测试  你写不写业务都无所谓,根据图的节点和边就可以静态的测试出图的结构!!
import_graph_app.get_graph().print_ascii()