一. 使用uv进行包管理

  1.1 安装uv和环境配置
    介绍:  
     为啥使用uv? uv包同步和下载速度更快! uv管理的项目有依赖配置信息 pyproject.toml 方便配置同步!!
     使用了uv不在使用pip了? 对  使用了uv还使用虚拟环境venv? 还需要使用!   uv [依赖下载和管理] + venv [当前项目独立环境配置]
       pip + venv   conda + venv   uv + venv
    安装: 
       pycharm 2025+版本 快速安装  [new project => uv -> 提示安装uv -> 选中安装路径即可]
       pycharm 2025以下版本   pip install uv  / pip show uv [version , location 安装的路径 ]
    配置环境变量: 
       开发软件 -> 系统环境变量 -> Path  [在任何位置都可以使用!]
       文件夹 > pip install uv -> 当前文件夹 / Path指定的文件夹 查找有没有叫pip可执行文件(软件)  |  唤醒pip软件 | 执行下载工作
       步骤1: pip show uv 查看uv的安装路径 [location]
       步骤2: 电脑 -> 属性 -> 高级系统设置 -> 环境变量 -> 系统环境变量 -> Path -> 新建 -> location(文件夹) -> 保存即可
       步骤3: 重新打开 cmd -> uv --version  1.显示uv的版本 配置完毕 2. uv 不是'内部或者外部命令'   
    镜像配置: 
        pip  / uv  / conda  -> 国外 -> 仓库 ->  国内的镜像 ->  国外 
       全局配置: 配置完毕,整个电脑所有项目都生效!! 
          C:\Users\登录用户名\AppData\Roaming\uv\uv.toml [

          ] [位置固定 乌龟得屁股]
            # 配置默认的 PyPI 镜像源 (清华源)
			[[index]]
			url = "https://pypi.tuna.tsinghua.edu.cn/simple"
			default = true
       项目配置: 写到项目配置文件(pyproject.toml),单个项目生效!!
          项目下 pyproject.toml 
            # 项目下配置环境变量(更推荐)
			[[tool.uv.index]]
			name = "tsinghua"
			url = "https://pypi.tuna.tsinghua.edu.cn/simple"
			default = true  

  1.2 构建uv管理的python项目

     目标: 使用uv包管理 + venv的python项目

     方案1: pycharm 25+ 可视化创建
        new project -> type -> uv -> python version 3.11 -> 创建  uv + venv
     方案2: pycharm 24- uv命令创建项目
        [没有项目文件夹/父文件夹中执行命令]
        uv init 项目名 [初始化uv管理的项目]     --> 除了配置文件带有其他的杂乱文件
        uv init 项目名  --bare [初始化uv管理的项目]  --> 纯净版本 pyproject.toml [推荐]
        -----------没有虚拟环境---------------
        [有项目文件夹,cd 项目文件夹 使用命令]
        uv venv    --> 项目创建虚拟环境文件夹 .venv  下载的依赖和python解释器 (使用你系统环境变量配置python解释器 3.12 .13)
        uv venv --python=3.11 --> 创建虚拟环境同时指定python解释器版本
        -----------激活当前虚拟环境,选中当前虚拟环境下的解释器--------
        [有项目文件夹,cd 项目文件夹 使用命令]
        .venv\Scripts\active..  --> (项目名) xxx
        ----------使用pycharm打开项目-----
        open ...
        (base)(项目名) -> 多层激活 conda / uv  -> conda取消管理  conda deactivate

  1.3 uv如何进行包管理(安装和卸载)

     批量同步: 项目环境已经设计完毕了! 存储到了项目pyproject.toml 
     	 步骤1: pyproject.toml粘贴到项目下
     	 步骤2: 使用同步命令 uv sync 
     	 步骤3: 查看和测试   uv tree | py脚本 导入...

         解释: pyproject.toml [1.项目基本信息 2.dependencies依赖信息 3.镜像信息] / uv.lock [记录第一次同步依赖版本 | 第一次添加 uv add]
              uv sync -> pyproject.toml dependencies依赖信息 -> 下载安装 -> .venv   [没有uv.lock]  问题: 下载了最新版本,版本漂移! 一个项目不同时期运行失败!!
              uv sync -> pyproject.toml [依赖] |  uv.lock [版本]-> 详细的具体的版本信息 -> 下载安装
              uv.lock -> 1.第一次同步 uv sync  2. 主动添加和修改版本 uv add / remove 
         问题: 
              warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         	  If the cache and target directories are on different filesystems, hardlinking may not be supported.
              If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.

              uv 第一次需要依赖 -> 镜像下载 -> 项目一份 | 缓存一份(cache)
              uv 第二次需要来   -> 缓存一份(cache)  ->  1. hardlink 软连接  2.full copy 复制文件 -> 项目一份

              获取缓存的依赖: 1. hardlink 软连接 快/节省空间 2.full copy 复制文件   
              默认行为: 同一个(缓存/项目)磁盘使用hardlink,否则full copy
              解决问题: cache  | 项目 放在一个盘符即可!!  setx UV_CACHE_DIR D:\uv-cache  | uv cache dir 

     独立安装:
        pip回顾: pip install 包名 最新版本  pip install "包名= >=..."  | pip uninstall 包名
        uv安装: 
        1. 完全兼容pip   uv pip install .. [uv要pip: 存量客户(pip) / 新增客户(没用过pip)]  (方式的包不会自动添加到pyproject.toml文件)
        2. 自己的安装方式 uv add 包 / "包=版本"   uv remove 包   [推荐]  (添加或者移除pyproject.toml)
        3. 批量 uv sync
    ------------------------------------------------
       1. 进步手册
       2. RAG介绍(作用/流程)
       3. 项目流程(导入 7个 / 查询 7  /  item_name ) 
       4. 项目技术选型 langgraph -> 受控
       5. uv安装 / 环境变量 / 镜像配置
       6. 创建uv管理项目  uv init 项目名 --bare  |  uv venv --python=x | 激活
       7. 依赖管理  uv sync  |  uv add / remove 
       目标: 项目创建完毕 ai_xx , 依赖同步完毕
    ------------------------------------------------
  1.4 知识库的项目构建完毕

二. 设计项目的基本结构

   app    --> 主程代码
       api      --> 写接口 / fastapi
       process  --> 节点和图编排 node函数 | langgraph
          import  --> 导入流程图
          query   --> 查询流程图
       rag      --> 节点相关的业务代码和实现 [节点+分页分离 高内聚 低耦合]
          import  --> 导入业务代码
          query   --> 查询业务代码
       resources  --> 放静态资源 [文件夹]
          prompts  --> 提示词 分析设计原理 / 优化空间
          htmls    --> 项目页面文件
       shared   --> utils 工具包
          工具包
       infra    --> 公开门面包 简化我们代码使用工具内容
          工具内容汇总
   test   --> 测试代码
   logs   --> 存储日志
   output --> 存储项目输出产物 pdf -> md

三. 导入初始化工具
 3.1 完成项目结构创建

 3.2 导入配置文件(.env) [资料/配置文件]
     .env  -> 真实配置, 不要提交到git仓库 1. 覆盖了别人的本地配置  2. 容易暴漏api_key
     .env.example -> 示例 key=没有值 需要提交到git仓库 / 改成.env 配置自己的参数
     为什么 .env 推荐放在项目根路径下!!  默认递归上下查找配置文件,根路径下一定能找到!!
     .env和系统环境变量的优先级问题!!  默认 系统环境变量更高! 建议  override=True: .env优先级高于系统环境变量 覆盖了...

 3.3 日志工具类导入和说明
   1. 什么是日志和日志工具(loguru)?
      日志记录项目核心运行过程和结果
      项目: [ 开发 - 测试 ] 开发工具 -  [ 生产 ] 服务器  -> 过程 -> 日志 -> 日志文件 <---- 我们
      为啥用日志工具?
          print(f"xxxxx{key}xxxx")  -> 控制台 | 没有紧要(日志级别)程度
          loguru ->  ergouzi(f"xxx{xxx}xxx") -> sink通道(输出的位置)更多 [控制台/文件/方法回调] | 更多的输出级别 debug info warning error exception
   2. 基本使用
      安装依赖
      uv add loguru [不需要了 uv sync]
      直接使用
      from loguru import logger

      移除一个通道: 默认输出控制台(输出格式默认格式 信息不够详细)  logger.remove(0)  移除第一个sink通道 控制台
      添加两个通道
         logger.add(控制台sink,format=格式配置)
         logger.add(文件地址,format=格式配置)

      logger.debug info warning error exception (输出的内容)  [默认也是输出到控制台]

   3. 日志输出界别的说明
      debug < info < warning < error = exception
      级别作用1: 严重程度的视觉体现
      级别作用2: 批量的控制开关  开发/测试: debug   生产: info warning error exception
      对应的级别要干对应的事: 级别越低,日志越多
         debug   : 详细体现代码的执行过程 [每行代码添加一个debug都不过分] <- 详细看到业务执行和对应详细过程
         info    : 核心节点过程体现 [进入  流程控制   结束]    <- 业务的执行流程和核心参数

               deg  parse(a,b):
                 logger.info(xxx a,b)
                 1  debug
                 2  debug
                 3  debug                   标准的项目 30%+的代码都是日志代码
                 4  debug
                 5  debug
                 logger.info(xxx result)
         -------------------------------------------------

         warning : 可能发生问题的位置/已经发生问题,但是这问题不影响业务的进行!
         error   : 发生了问题,进行报错并且业务终止

         导入流程:  pdf文件 (pdf文件地址 local_file_path) ->  md文件 -> output文件夹 (local_dir)
            参数校验:
               if not local_file_path:
                   是否为空
                   logger.error("输出业务终止的原因....")
                   raise ValueError(xxxxxx)     -> 全局异常处理 -> 统一结束业务

               if not local_dir:
                   是否为空
                   输出的默认位置
                   local_dir = ROOT_PATH  / "output"  -> mkdir()
                   logger.warning("业务的出现问题,但是能修补,以后少这样!!")
         --------------------------------------------------
         exception: 报错了, 我们捕捉到的异常! 更详细的打印异常堆栈信息

         try
            xxx
         except Xxx as e:
            logger.exception(e)  -> error -> 更详细的报错信息
   4. 配置文件解读
        # 控制台日志：True=开启/False=关闭，级别可选(DEBUG/INFO/WARNING/ERROR/CRITICAL)
        # 控制台输出开关 logger  LOG_CONSOLE_ENABLE -> 控制台
        LOG_CONSOLE_ENABLE=True
        # 控制台输出的日志级别  DEBUG < INFO < WARNING < ERROR
        LOG_CONSOLE_LEVEL=DEBUG

        # 日志配置
        # 文件日志：True=开启/False=关闭，级别与控制台可独立设置
        # 文件输出控制
        LOG_FILE_ENABLE=True
        LOG_FILE_LEVEL=INFO
        # 日志文件保留天数（自动删除过期日志，避免磁盘占满）
        LOG_FILE_RETENTION=7 days
   5. 装饰器说明
        @node_log(节点名)
        @step_log(步骤名)
        意义: 1. 简化关键日志的打印和标准化输出格式 2. 装饰器作为全局异常处理 (业务代码有问题 raise 抛出异常)

        @node_log(节点名)      @step_log(步骤名)
        node                  step
   6. 基本使用示例
       from app.shared.runtime.logger import logger
       logger.info("xx{}xxx",参数)

 3.4 提示词和加载工具
     prompts / 静态文件 -> resources
     load_prompt.py -> shared / runtime /
     使用: content:str = load_prompt("提示词文件名不要加后缀名", {key必须要对应}="占位符的值",{key必须要对应}="占位符的值")

 3.5 config和加载工具
     资料 / 配置加载类 / config  ->  shared / config
     config
        不同方向接值.py
        不同方向接值.py
        不同方向接值.py
        不同方向接值.py
        不同方向接值.py
           一个类型 class 类:
                    属性:类型
           一个类对象存储具体的值:
                 对象 = 类(
                    属性= os.get 没有这么   -> config/common.py -> def env_str(name: str, default: str = "") -> str:
                    属性=
                 )
     注意:  common.py /  load_dotenv(override=True)
 3.6 其他的shared工具导入
     资料: shared工具类 -> shared / clients | model | tool | utils
 3.7 公共配置文件门面
      infra
         config类  [1,2,3,5] -> infra_config

四. 项目推送到gitee并且更新进度手册
 4.1 每个人在进度手册创建两个行 [名字/两个gitee可视化(浏览器) 切记开源]
 4.2 本地项目创建好忽略文件
     全局 [不推荐]
         电脑中,创建一个忽略文件 .gitignore  标记忽略的内容
         修改git的全局配置,指定这个忽略文件
     项目
         项目根路径下 .gitignore
         使用插件创建 -> python | java | 前端  ->  创建忽略文件 ->  添加项目类型的通识忽律内容

     安装插件和使用
        安装: settings / plugins / market  .ignore 安装
        使用: 项目 / 右键 / new / ignore files / git / python / 生成
        添加: doc logs output
 4.3 被git管理和推送到远程
      初始化git仓库  git init
      红色 -> 工作区 -> 没有添加到暂存区   git add .
      绿色 -> 暂存区 -> 版本库  git commit -m "xx"
      关联远程仓库 -> 右键 -> git -> manager remotes -> +  git remote add 别名 地址
      push推送到远程即可

=======================
 今日内容简单总结:
    rag和项目理解: rag是啥?作用?所用的模型?基础流程? 项目设计的节点!  [不是今天的目标/项目的目标]
    项目搭建: uv 安装 / 环境配置 / 镜像配置 / uv项目创建  uv init 项目名 --bare --python=3.11 | uv venv --python=版本 / 依赖同步 pyproject.toml uv.lock  /  uv sync  uv tree  uv add / remove  uv pip
    项目结构: app api rag process resources shared infra / test
    项目基础: 配置文件.env .env.example  | 日志 [工具类作用,配置,装饰器,基本使用(日志级别)] | 提示词 | 配置文件 | config_infra  属性=默认值 引用类型 问题+解决
    项目git: 忽律文件 / 初始化 / 本地提交 / 远程提交

    最终的要求: 每个人在进度手册 按组创建两个条目和gitee地址!!