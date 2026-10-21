

一. 内容回顾
   1.1 项目简单介绍和rag说明
   1.2 项目环境搭建(uv/项目构建/依赖导入)
     技术点1: uv的基本使用 pip install uv  pip show uv  配置环境变量  配置清华镜像
     技术点2: uv的项目管理 uv init 项目名 --bare --python=3.11   uv venv --python=3.11
     技术点3: uv的项目同步 pyproject.toml | uv.lock   uv sync
     技术点3: uv的依赖管理  1. 支持pip  uv [pyproject.toml] 2. uv add / remove 依赖 "= > >=3.11,<=3.14"
   1.3 项目基础内容导入
     项目结构  infra == shared
     导入配置文件 .env
     导入日志工具 loguru  输出不同sink的内容  debug info warning error == exception  @node_log @step_log
     提示词文件
     shared工具
     创建配置文件infra [自己写 / default_factory默认值 -> 基础类 @dataclass BaseModel ]

二. 导入业务分析&向量数据库设计  [业务回顾]

   2.1 导入节点流程
      节点1: 文件类型识别分发(node_entry) : 不同类型的文件识别! 主要靠后缀名识别! 现在的项目md/pdf,以后增加类型,添加识别逻辑即可!
      节点2: 特殊类型单独处理(node_pdf_to_md): 非结构化数据 -> 转成 -> 结构化文本数据,后续扩展其他的类型 图片/word正常添加节点即可!
      节点3: 结构化数据特别单元处理(node_md_img): 图片内容的处理 1. 图片地址转成http  2. 图的意图进行识别
      节点4: 准备好的长数据切割(node_document_split) : rag的核心 将长文档 切割成合理的切块!
      节点5: 锁定范围的主体识别(node_item_name_recognition): 识别文档主体,用于缩小搜索范围, 因为主体识别一般前几个章节可以确定! 切割完毕!前几个切换给模型,省token!
      节点6: 进行数据向量化处理(node_embedding): 生成稠密和稀疏向量
      节点7: 向量库的持久化处理(node_import_milvus): 将数据进行持久化存储
   2.2 向量数据库设计
      文档级别 -> 每个文档唯一标识 item_name
         pk file_title[文件名] item_name dense_vector  sparse_vector
      切片级别 -> 存储文档所有切片内容,关联的item_name
         chunk_id content item_name dense_vector sparse_vector [title parent_title part]

三. 导入图state设计和图构建测试  [回顾langgraph  state 节点 边 图对象编译]

   3.1 state的设计和说明
       前置1: langgraph ->  state -> 状态 -> 共享数据 -> 用于节点之间传递参数
       前置2: state的数据类型 -> 类 -> TypedDict / BaseModel
       前置3: state的类型  全局state / 输入state  / 输出state / context state   上下文环境 只读 业务支撑 例如: 任务的唯一标识 task_id / 账号 / role

              StateGraph(schema_state=A,input_state=B,output_state=C)

              class A:
                 1
                 2
                 3
              class B:
                 1
              class C:
                 3
              class D:
                 4

              from langgraph import Runtime -> 装了context   Runtime  context:泛型

              node1(A , 变量: Runtime[D])
                 print(A -> 1)
                 变量.context.4

              node2(A)

              node3(A) -> A
                 return {1,2,3}

              1.执行图对象  result_state {3:值} = graph.compile().invoke(  input = {1:值,2:值} , context = {4:task_id}  )
       state的设计和实现: [也要写]
          12个属性
          位置: app/process/import_/agent/state  ImportGraphState  12属性 + 1模板 + 2个方法

            from typing import TypedDict, Any
            import copy

            class ImportGraphState(TypedDict):

                # 12个属性
                # 任务标识 -> context_state -> task_id
                task_id:str

                # 输入文件和输出文件夹
                local_file_path:str # 输入的文件地址  start ->  local_file_path->  node_entry
                local_dir:str  # 输出文件的文件夹地址 output

                # 标记文件类型
                is_md_read_enabled:bool # 是不是md
                is_pdf_read_enabled:bool # 是不是pdf

                # 存储对应类型的文件地址
                md_path:str  # 专门存储md文件地址
                pdf_path:str # 专门存储pdf文件地址

                # 存储数据内容
                md_content:str # md的文本内容 后续用于切割
                item_name:str  # 文件的唯一标识
                file_title:str # 文件名 去掉后缀名  xx.txt  -> xx

                # 切片后的数据
                chunks:list[dict[str,Any]] # 切片内容 content item_name title...  {content:x,item_name:x}
                embeddings_content:list[dict[str,Any]] # 装生成向量的切片内容 稠密和稀疏

            # 定义了一个对象模板 赋予少量的默认值
            graph_default_state: ImportGraphState = {
                "task_id": "",
                "is_pdf_read_enabled": False,
                "is_md_read_enabled": False,
                "local_dir": "",
                "local_file_path": "",
                "pdf_path": "",
                "md_path": "",
                "file_title": "",
                "md_content": "",
                "chunks": [],
                "item_name": "",
                "embeddings_content": [],
            }
            # 提供了两个快速创建对象的方法
            def create_default_state(**kwargs)->ImportGraphState:
                """ 快速创建一个指定属性的state对象,并返回新的对象 """
                # **kwargs -> 动态 -> key=value传递参数 -> 要求 key = 属性名 -> kwargs 字典
                new_state: ImportGraphState = copy.deepcopy(graph_default_state)
                # for key,value in kwargs.items():
                # for key in kwargs:
                new_state.update(kwargs)  # dict.update(dict) 相同的字段自动更新
                return new_state


            # create_default_state ->  指定赋值属性  -> state

            def get_default_state()->ImportGraphState:
                """ 快速返回模板对象,不修改属性,返回都是新的对象"""
                new_state:ImportGraphState = copy.deepcopy(graph_default_state)
                return new_state

            # get_default_state -> state -> 模板state对象 其他的属性后续再修改

            # copy
            # import copy
            # 浅copy: 第一层属性  新的对象 =  copy.copy(模板对象)
            # 深copy: 嵌套属性   新的对象 =  copy.deep_cope(模板对象)

   3.2 图节点导入

       节点: 1. 简单的方式 函数  def 函数名(state,Runtime): 业务 return {}   -> langgraph -> state合并
            2. 类的对象  Class 节点类:  __call__(self): 业务逻辑 return {}
       区别:
            1.批量创建节点的时候! 函数节点会出现函数延迟错误!!   for [1,2,3,4,[5]]:  1 -> node函数(1)  2-> 节点函数(2) .... -> 5个5
                                                          for [1,2,3,4,[5]]:  类(1)  类(2) -> __init__ 会立即调用
            2. 节点 -> 业务+数据集成体   函数 -> 业务 | 类对象  属性 + __call__ 函数
            3. state -> context_state  函数(x:Runtime[context类型])   ||  父类  __init__(self)  self.context = context_state <- 子节点类
       项目节点:
           节点:  app/process/import_/agent/  state | main_graph | nodes [文件夹]  / 节点.py 7  / 节点函数 1
                  节点函数 1  - 调用 - 业务方法 1
           业务:  app/rag/import_/ 业务.py 7 / 业务方法 1

   3.3 构建图对象
       位置: app/process/agent/main_agent.py -> graph对象
       步骤:
             1. 创建图的构建对象   builder =  StateGraph(state)
             2. 添加节点   builder.add_node(函数/对象) | add_node("节点",函数/对象)
             3. 添加边     builder.add_edge("1","2")  /   builder.add_conditional_edge("开始节点",路由函数,path_map={})
             4. 编译图对象  graph =  builder.compile()
       代码:
            from langgraph.graph import StateGraph, END
            from app.process.import_.agent.state import ImportGraphState
            from app.process.import_.agent.nodes.node_entry import node_entry
            from app.process.import_.agent.nodes.node_pdf_to_md import node_pdf_to_md
            from app.process.import_.agent.nodes.node_md_img import node_md_img
            from app.process.import_.agent.nodes.node_document_split import node_document_split
            from app.process.import_.agent.nodes.node_item_name_recognition import node_item_name_recognition
            from app.process.import_.agent.nodes.node_bge_embedding import node_bge_embedding
            from app.process.import_.agent.nodes.node_import_milvus import node_import_milvus
            from app.shared.runtime.logger import  logger

            # 1. 创建图的构建对象
            import_builder = StateGraph(state_schema=ImportGraphState)

            # 2. 添加节点
            import_builder.add_node("node_entry",node_entry)
            # import_builder.add_node(node_entry)
            import_builder.add_node("node_pdf_to_md",node_pdf_to_md)
            import_builder.add_node("node_md_img",node_md_img)
            import_builder.add_node("node_document_split",node_document_split)
            import_builder.add_node("node_item_name_recognition",node_item_name_recognition)
            import_builder.add_node("node_bge_embedding",node_bge_embedding)
            import_builder.add_node("node_import_milvus",node_import_milvus)

            # 3. 添加边 [静态边/条件边]
            # START -> 自己节点 -> END
            # import_builder.add_edge(START,"node_entry")
            import_builder.set_entry_point("node_entry")

            def after_node_entry(state:ImportGraphState) -> str:
                """
                state -> 值 -> 返回目标节点名
                :return: 字符串 目标节点的名字 node_pdf_to_md | node_md_img | END
                """
                if state.get("is_md_read_enabled"):
                    # 不为空 且 为True
                    # 文件就是md类型
                    # 日志: 前因 + 后果 + 核心参数(佐证)
                    logger.info(f"传入的文件是md格式,md_path:{state.get('md_path')},后续跳转到node_md_img节点!")
                    return "node_md_img"
                elif state.get("is_pdf_read_enabled"):
                    # 不为空 且 为True
                    # 文件就是md类型
                    logger.info(f"传入的文件是pdf格式,pdf_path:{state.get('pdf_path')},后续跳转到node_pdf_to_md节点!")
                    return "node_pdf_to_md"
                else:
                    logger.warning(f"当前项目只支持pdf和md格式,local_file_path:{state.get('local_file_path')},后续跳转到END节点!")
                    return END

            """
               langgraph 静态 add_edge("1","2") 一定会执行
               langgraph 条件 add_conditional_edges("起始节点[节点执行完毕]",函数 return 目标节点[逻辑函数], path_map:dict = {key:目标节点,key:目标节点...}  -> 静态测试看
               条件边的第三个参数:  1.静态测试,必须显示的写path_map  2. 不是静态测试,但是路由函数返回的值不等于目标节点
                          语法:  { key等于路由函数可能返回值 : "目标节点名称"   }

            """
            import_builder.add_conditional_edges("node_entry",after_node_entry,{
                "node_pdf_to_md":"node_pdf_to_md",
                "node_md_img":"node_md_img",
                END:END
            })


            # 静态边
            import_builder.add_edge("node_pdf_to_md","node_md_img")
            import_builder.add_edge("node_md_img","node_document_split")
            import_builder.add_edge("node_document_split","node_item_name_recognition")
            import_builder.add_edge("node_item_name_recognition","node_bge_embedding")
            import_builder.add_edge("node_bge_embedding","node_import_milvus")
            import_builder.add_edge("node_import_milvus",END)

            import_graph_app = import_builder.compile()

       测试:
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

四. 文件类型识别节点node_entry  [感受项目节点处理流程]

   4.1 宏观介绍接口和业务的调用流程

       process
          nodes 节点 -> langgraph图编排
               |
           业务代码调用
               |

        # 装饰器的作用: 打印日志
        @node_log("node_entry")
        # 节点函数 ( state 全局共享域 |  runtime context)
        def node_entry(state: ImportGraphState) -> ImportGraphState:
            """
            节点: 入口节点 (node_entry)
            为什么叫这个名字: 作为图的 Entry Point，负责接收外部输入并决定流程走向。
            """

            # add_running_task  add_done_task 函数 -> 来自于我们自定义的工具类  shared / utils / task_utils.py [大致了解!web接口的时候再详细说]
            # 简单的理解: 将进行中或者完成的节点存储到容器中 -> 容器 <- fastapi节点读取 <- 轮询 1s <- 前端页面
            # 为啥不是单独添加节点名,还添加了一个task_id?  底层存储使用字典,为每个客户端存储一个对应的列表! task_id客户端的标识!!
            #  {task_id: str}  -> {task_id:list}
            add_running_task(state["task_id"], "node_entry")
            # langgraph -> 节点函数 -> 业务函数
            # 参数: state  业务操作 数据操作  返回: state
            state = resolve_input_file(state)
            add_done_task(state["task_id"], "node_entry")

            # state数据返回  langgraph进行合并传递到下一个节点
            return state
       rag
          services  -> 业务代码

   4.2 实现第一个节点node_entry
      节点作用:
         识别传入文件的类型! local_file_path 根据地址,识别文件类型! 最终修改对应的文件状态(state)!
         后续会有一个条件边,根据我们修改的值,完成指定节点的转发!
         理解, 后续添加其他的文件处理,也需要在这个节点添加业务和节点分发!
      节点参数: state
         传入: local_file_path  task_id
         生成: is_md_read_enabled is_pdf_read_enabled md_path pdf_path file_title
      节点步骤:
         1. 先从state读取使用的数据 local_file_path  task_id  注意: 别要直接 [] 避免KeyError 使用get...
         2. local_file_path做非空判断  注意: 必须判断,不要过度!
         3. 不为空进行后缀名判断 md / pdf -> 修改对应的值 else 既不是md又不是pdf 打印日志..
         4. 将地址转成Path对象 (os.path) 快速获取文件file_title
         5. state属性更新
         6. 返回state
      节点技术:
         Path使用分三步:
          1. 创建对应的Path对象
             x:Path = Path( 字符串地址 )  获取地址对应的Path对象
             x:Path = Path( Path对象  )  暂时用处不大!!
             x:Path = Path()            获取当前文件所在的文件夹  linux pwd
             x:Path = Path(__file__)    获取当前文件的Path地址
             x:Path = path对象 / "字符串地址" / "字符串地址"     ROOT_PATH / "output"
          2. .属性
             .name    文件的完整文件名  info.pdf
             .stem    获取文件名部分    info
             .suffix  获取后缀名部分    .pdf
             .parent  获取父Path对象   Path(__file__).parent.parent
             .parents 获取所有的父文件夹 Path(__file__).parents[1] = [import_,rag,app,项目根地址..]
          3. .方法()  创建一个文件夹 查询文件是否存在

五. pdf文件解析节点node_pdf_parse [minerU http  requests/httpx Path 文件解压操作等等 ]


今日内容:
    1. 进步手册说明 默认值问题 default_factory | git的ssh配置问题
    2. 简单回顾 uv的基本使用
    3. 导入流程7个节点 | 两个向量数据库的集合
    4. 创建state -> 四种state类型 [晚上(测试)代码可以不写,必须粘贴走一遍 03_test_langraph_state_type.py]
    5. 分析state 12个属性 + 实现  state + 1 + 2 + 深copy  [写]
    6. 导入节点和业务  -> 节点的定义形式 函数节点 | 类节点
    7. 定义导入的图  langgraph使用回顾  图的定义和边以及条件边的参数path_map参数 [写]
    8. 静态和动态测试  [写]
    7. 第一个节点的实现 node_entry [写][Path]