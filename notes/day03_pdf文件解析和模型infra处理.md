

一. 内容回顾
   1.1 回顾导入业务节点和向量数据库设计
   1.2 分析state12个属性以及介绍四种state类型 [state_schema/context_schema/input_schema/output_schema]
   1.3 定义state / 深copy / 动态参数 **  / 字典类型更新 update
   1.4 导入图节点和业务节点  [节点固定格式  @node_log("节点名") def 节点函数(state)  add_running_task(task_id,"节点名") 调用业务函数  add_done_task(task_id,节点名)]
   1.5 创建对应图结构  langgraph  1.创建一个状态图构建对象 StateGraph(state_schema)  2. 添加节点 add_node(函数/对象) ("节点名",函数/对象)  3. 添加边  add_edge("字符串") / add_conditional_edge(1,2,3 -> path_map -> 1. 静态测试 2. 路由函数返回的不是节点名)   / 编译对象 compile
   1.6 编写第一个节点 node_entry -> Path (python3.4文件的操作对象) 把一个地址变成一个对象的思路! 1. Path(__file__) Path() pwd  Path(路径)  Path / xx   2. .属性  .name .stem .suffix .parent .parents  3. .函数  is_file()  is_dir()  exists()  mk_dir()  read_bytes() read_text() write_bytes() write_text()  iterdir()  glob()  rglob()
   1.7 节点测试

二. pdf文件解析节点node_pdf_to_md
  节点作用:
        将本地pdf文件,利用minerU,解析成md文件!
        最终存储到项目下 /output/文件名命名的文件夹 / 原文件名.md | images/图片
        修改state -> md_path => md地址
  节点参数:
     传入:  pdf_path / local_dir / task_id
     生成:  md_path
  节点步骤:
     1. 准备工作  申请minerU token  修改.env配置  -> infra/config/provider/infra_config . mineru .
        MINERU_API_TOKEN=eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI3NjUwMDY4NiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3MzY3MDk2OSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMTBkYTM3MTgtMzA3YS00ODdkLWJhNDEtZjNkYzlmMGQ3ZmE5IiwiZW1haWwiOiIiLCJleHAiOjE3ODE0NDY5Njl9.9DF0FHvQYaK6NRnOVG87V_IYToHPRcyHcQd-tuXETuPIJzVV6h6PMc3RtY5zeaIN7LiPRobziXqAKWoDNl3ueA
        MINERU_BASE_URL=https://mineru.net/api/v4
     2. 添加一些常量配置 [vlm / 轮询的间隔 / 最大等待时间 ..]
        rag/import_/config.py -> 常量
        # MinerU 模型版本配置（vlm = 视觉语言模型，适合PDF/图片高精度解析）
        MINERU_MODEL_VERSION = "vlm"
        # MinerU 任务轮询最大超时时间（单位：秒），超过则判定任务失败
        # 600 -> 一个pdf 约等于 1秒
        MINERU_POLL_TIMEOUT_SECONDS = 600
        # MinerU 任务轮询间隔时间（单位：秒），每隔多久查询一次任务状态
        MINERU_POLL_INTERVAL_SECONDS = 3
        # MinerU 文件下载超时时间（单位：秒），下载文件超过此时长则中断
        MINERU_DOWNLOAD_TIMEOUT_SECONDS = 600
     3. 核心参数校验 pdf_path  local_dir
        validates_pdf_paths(state:ImportGraphState) -> tuple[Path,Path]
        3.1 从state中获取pdf_path和local_dir地址 -> str
        3.2 非空校验 如果pdf_path为空 error / raise  | 如果 local_dir为空  给与默认值 项目根地址 / "output" -> state['local_dir'] = local_dir
        3.3 将pdf_path和local_dir转成Path对象,方便后续操作 -> Path
        3.4 检查pdf_path_obj是否真实存在 exists() | is_file() 有效[存在]的文件  不是有效文件 error raise
        3.5 检查local_dir_obj是否是真实存在  is_dir() ! 不是有效 mk_dir()
        3.6 return pdf_path_obj , local_dir_obj
     4. minerU处理流程 [申请上传文件地址]
        向minerU发起申请,获取上传文件地址
        apply_mineru_get_upload_url(pdf_file_name:str) -> tuple[str,str]
        4.1 组装对应的请求头 (token)
        4.2 组长对应的请求体json数据(请求参数)
        4.3 向对应的接口发起post方式请求,并等待[阻塞]获取结果
        4.4 判断http协议网络状态status_code
        4.5 判断业务状态码code
        4.6 获取目标结果batch_id/upload_url地址
        4.7 返回结果即可
     5. minerU处理流程 [上传文件]
        向指定的文件服务器的地址,上传文件,注意使用的请求方式为put
        upload_file_to_url(upload_url地址:str,pdf_path_obj:Path) -> None:
        5.1 读取上传文件的数据pdf_path_obj->字节的数据
        5.2 向指定的地址发起put请求,传递pdf文件数据
        5.3 判断响应状态码,不是200抛出异常! [本次只需要判断http状态码,不需要判断业务code! 本身就是不是minerU业务接口,文件服务器的上传地址]
     6. minerU处理流程 [轮询获取解析结果->zip_url]
        通过batch_id轮询获取解析结果,获取的结果是一个url -> zip文件下载的地址   pdf -> minerU解析 -> zip -> zip_url
        poll_mineru_zip_url(batch_id:str) -> str:
        6.1 接收常量参数 临时变量接收值 最大轮询时间 / 轮询间隔时间 / 记录起始时间
        6.2 死循环 while True:
            6.2.1 有没有超过最大等待时间 [1~N]
            6.2.2 向指定的地址请求查询解析状态
            6.2.3 判断网络状态码status_code != 200  [判断是否可以给与机会(5xx),可以等待重试 / 其他的也需要抛出异常终止轮询 ]
            6.2.4 判断业务状态码code != 0 [需要抛出异常终止轮询]
            6.2.5 判断文件的解析状态state
                  done -> zip -> return
                  fail -> 失败 -> raise
                  else -> 休眠 再次请求
     7. 文件的下载和解压
     8. 修改state -> md_path赋值
     9. 返回本次state

  节点技术:
     1. minerU使用和api_key申请
        1.1 为啥选择minerU
            认可度高 / 更新实时  /  支持的文件类型多 / 免费开源
        1.2 基本使用步骤
            接口方式: 1. 在线接口api调用(minerU的服务器资源)[文件安全] 2. 本地部署minerU(自己的服务器)  https://opendatalab.github.io/MinerU/zh/quick_start/
            步骤1: 向minerU发起请求,申请文件解析的上传地址 [api_key(token) minerU免费,需要认证 |  申请文件上传链接的数量 ...]   upload_url / batch_id
            步骤2: 向指定的地址,传递文件数据   [开始解析了....] upload_url
            步骤3: 获取本次解析的结果 [轮询/回调] batch_id
        1.3 api_key申请(token)
            https://mineru.net/apiManage/token
        1.4 模式选择问题
            pipeline（默认） : ocr视觉识别算法 速度更快,但是不识别语义和图片含义! 是简单排版的纯文字类的pdf/图片!
             vlm(推荐)      : 视觉模型,利用模型进行全局的识别,也支持图片的语义处理! 速度慢于pipeline
            MinerU-HTML    : 专门处理html文件格式
     2. http协议回顾
        2.1 http介绍和作用
            HTTP(HyperText Transfer Protocol) 超文本 -> 字符 + 字节  传输 ->   客户端  == 服务端   协议 ->  规定,客户端和服务端传递数据格式和时序
            HTML(HyperText Market Language)
                    ---->   请求数据包 --->
            客户端                             服务端 (业务逻辑)   HTTP协议是一次性的!
                   <----  响应一个响应数据包 ---
        2.2 http协议的数据报(包)
            请求数据包
                请求行:   请求方式[空格]请求地址[空格]协议版本\n  -> 请求目标和方式
                请求头:   key = value                        -> 客户端的额外信息  客户端类型/客户端传递数据大小/需要返回文件格式
                ...
                请求头:   key = value                        -> 固定的key   host-agent=客户端类型...
                请求空行: \n\n                               ->  分割请求头和请求体
                请求体:   字节/字符数据                        -> 客户端传递的数据 json / 文件
            响应数据包
                状态行:   协议版本[空格]状态码[空格]状态值\n      -> 服务器响应状态 200 202 304 405 500 502
                响应头:   key = value                        -> 服务端的额外信息 key也是固定 content-length  content-type
                ...                                         ->                content-disposition = attachment;filename=文件名
                响应头:   key = value
                响应空行: \n\n
                响应体:   响应数据 字符/字节数据                 -> 响应图片
        2.3 http协议的请求方式
            客户端 --> 请求数据包 请求数据方式 ---> 服务端
            get / post / put / delete
            问题:应该如何选择请求方式? 请求方式到底有什么影响?
              1. 影响请求数据包的格式(不影响响应数据包)
                 get / delete -> 请求数据包 -> 2部分 -> 请求行 请求头
                 post/ put    -> 请求数据包 -> 4部分 -> 请求行 请求头 空行 请求体
              2. 请求方式对应成对应请求动作
                 文件 -> post / put
                 get 获取 delete 删除 post 上传  put 更新
                 也要考虑对应的数据语义 新增 post  更新 put 删除 delete 查询 get [restful]
            结论:
              1. get和delete速度快于post/put? 正确            数据结构更简单
              2. 传递字节数据必须使用post/put?  正确            post/put才有请求体(请求体本质是流传递任何数据)
              3. post/put(传递数据)安全性高于get/delete? 正确   get/delete 请求行 url?路径传递参数,直接暴漏在客户端
            传递参数方式:
              key=value -> params ->  url? key     -> get/delete   post/put
              path      -> path   -> /path/1       -> get/delete   post/put
              json      -> json   -> {'key':value} -> post/put 请求体
              字节数据    -> 文件   -> 二进制的流      -> post/put
            如何根据参数选择请求方式:
              1. 非字符数据必须             post/put
              2. 隐私字符数据               post/put
              3. 超过2kb大小的非隐私字符串   post/put
        2.4 http协议的响应状态码含义
            1xx : 中继状态  不用考虑 本次请求尚未完成
            2xx : 成功状态  200 完整成功 / 202 部分请求数据返回成功 [端点下载]  不用考虑
            3xx : 间接成功  304 重定向-> 早期购物完整除了淘宝,不支持支付!  不用考虑
            4xx : 客户端问题  400 bad request  404 地址错了  405 请求方式错了  -> 客户端调整
            5xx : 服务端问题  500 502 ..服务器内部异常 服务端的代码,出现异常,抛给了uvicorn! -> 服务端调整
                前端(客户端) ==  (服务端) 后端 (客户端) == minerU (服务端)
     3. requests网络请求工具说明
        3.1 requests介绍
            很古老,http请求工具! 可以向服务端发起具体的请求和获取对应结果!
            特点: 线程阻塞 同步io [多协程: 慎用 httpx协程级别]
        3.2 向服务端传递数据
            import requests

            requests.request(method="get/post...") / get post put delete() -> 底层 requests.request(method="get/post...")
            requests.post put(url/x/x,params={key:value},headers={key:value},json={key:value},data=字节数据,timeout=秒)
                 url?key=value params  path  请求体 json 请求体 字节数据 | url 请求头  获取响应都是一样
            requests.get  delete(url/x/x,params={key:value},headers={key:value},timeout=)
                 url?key=value params  path | url 请求头  获取响应都是一样

                 (
                   url    -> 请求地址 可以在地址上拼接 / 路径参数
                   params -> 路径?key=value&key=value  = {}
                   json   -> 请求体 json字符串  {}
                   data   -> 请求体 字节数据 文件
                   headers-> 请求头 {}
                   timeout-> 超时时间 单位秒 不传递默认永远不超时 ...
                 )

        3.3 接收数据段响应数据
            response [服务器返回的数据结构] = requests. get / post / put / delete()  <-阻塞
            response [状态行 -> 状态码 / 响应体 -> 响应数据 ]
            状态码本次请求是否成功还是失败:
               response.status_code -> 1 2 3 4 5xx
            获取响应数据(响应数据获取都在状态码判断成功以后获取):
               @property
               response.text()     : 获取响应的字符串 "{json}" -> dict =  json.loads(字符)  "我爱你中国!!"
               @property
               response.content()  : 响应的字节数据/文件
               response.json()   : 获取响应的(json)字符串,自动转成字典,可以直接取值!!
            解析结果流程:
              1. 判断http网络状态码  response.status_code == 200
              2. 判断业务状态码      response.json().get("code",-1) == 0
              3. 获取解析结果        ....

今日内容:
   1. pdf解析接口的所有代码 实现2遍!!!
   2. http通信协议 [介绍/作用/数据包/请求方式/状态码]  ||  requests工具怎么发送http协议请求
   3. minerU的使用步骤 1.申请地址 2.上传文件 3.轮询获取解析结果  4. 扩展 callback配置 (checksum)
        from fastapi import FastAPI, Request
        import hashlib
        import json

        app = FastAPI()

        # ========== 这里改成你自己的UID和seed（MinerU个人中心获取） ==========
        MINERU_UID = "你的uid"
        MINERU_SEED = "你的seed"
        # ====================================================================


        def calc_sha256(raw_str: str) -> str:
            """计算 sha256"""
            return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


        @app.post("/callback")
        async def mineru_callback(request: Request):
            # 1. 读取MinerU POST过来的整个JSON体
            body = await request.json()
            print("收到MinerU回调原始body：", body)

            checksum_from_mineru = body.get("checksum")
            content_str = body.get("content")  # 注意：content是JSON字符串！不是dict

            if not checksum_from_mineru or not content_str:
                # 参数缺失，返回非200，MinerU会重试
                return {"msg": "参数不全"}, 400

            # 2. 校验签名：uid + seed + content字符串 拼接后sha256
            sign_source = f"{MINERU_UID}{MINERU_SEED}{content_str}"
            local_checksum = calc_sha256(sign_source)

            if local_checksum != checksum_from_mineru:
                print("签名校验失败！可能被篡改")
                return {"msg": "checksum 校验不通过"}, 403

            # 3. 把content字符串转成Python字典（就是任务data结果）
            try:
                task_data = json.loads(content_str)
            except Exception as e:
                print("content json解析失败", e)
                return {"msg": "content解析错误"}, 400

            # ========== 业务逻辑在这里写 ==========
            # task_data 就是MinerU解析结果，和轮询接口返回的data一致
            print("解析任务结果：", task_data)
            # 比如：保存数据库、发送消息、后续RAG入库等
            # ======================================

            # 返回200，MinerU判定接收成功，不再重试
            return {"code": 0, "msg": "ok"}, 200