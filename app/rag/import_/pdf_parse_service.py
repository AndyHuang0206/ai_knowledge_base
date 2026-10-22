import time

from app.process.import_.agent.state import ImportGraphState
from pathlib import Path

from app.rag.import_.config import MINERU_MODEL_VERSION, MINERU_DOWNLOAD_TIMEOUT_SECONDS, MINERU_POLL_TIMEOUT_SECONDS, \
    MINERU_POLL_INTERVAL_SECONDS
from app.shared.runtime.logger import logger, PROJECT_ROOT
from app.infra.config.providers import infra_config
import requests
import shutil  # shell util  linux工具

"""
 validates_pdf_paths(state:ImportGraphState) -> tuple[Path,Path]
        3.1 从state中获取pdf_path和local_dir地址 -> str
        3.2 非空校验 如果pdf_path为空 error / raise  | 如果 local_dir为空  给与默认值 项目根地址 / "output" -> state['local_dir'] = local_dir
        3.3 将pdf_path和local_dir转成Path对象,方便后续操作 -> Path
        3.4 检查pdf_path_obj是否真实存在 exists() | is_file() 有效[存在]的文件  不是有效文件 error raise
        3.5 检查local_dir_obj是否是真实存在  is_dir() ! 不是有效 mk_dir()
        3.6 return pdf_path_obj , local_dir_obj
"""


def validates_pdf_paths(state: ImportGraphState) -> tuple[Path, Path]:
    # 3.1 从state中获取pdf_path和local_dir地址 -> str
    pdf_path: str = state.get("pdf_path")
    local_dir: str = state.get("local_dir")
    # 3.2 非空校验 如果pdf_path为空 error / raise  | 如果 local_dir为空  给与默认值 项目根地址 / "output" -> state['local_dir'] = local_dir
    if not pdf_path:
        # 前因  后果  关键参数
        logger.error(f"pdf_path地址为空!业务无法继续,提前终止!")
        raise ValueError(f"pdf_path地址为空!业务无法继续,提前终止!")
    if not local_dir:
        local_dir = PROJECT_ROOT / "output"
        logger.warning(f"local_dir没有赋予默认值,配置默认输出地址为:{local_dir},业务继续进行!!")
        state['local_dir'] = str(local_dir)  # state标准 类型就是字符串
    # 3.3 将pdf_path和local_dir转成Path对象,方便后续操作 -> Path
    pdf_path_obj: Path = Path(pdf_path)
    local_dir_obj: Path = Path(local_dir)
    # 3.4 检查pdf_path_obj是否真实存在 exists() | is_file() 有效[存在]的文件  不是有效文件 error raise
    # is_file() 存在 文件  exists() 存在
    if not pdf_path_obj.is_file():
        logger.error(f"pdf_path路径地址为:{pdf_path},但是检查没有真实对应到文件!业务无法继续,提前终止!!")
        raise FileNotFoundError(f"pdf_path路径地址为:{pdf_path},但是检查没有真实对应到文件!业务无法继续,提前终止!!")
    # 3.5 检查local_dir_obj是否是真实存在  is_dir() ! 不是有效 mk_dir()
    if not local_dir_obj.is_dir():
        logger.warning(f"local_dir路径地址为:{local_dir},但是没有具体的文件夹,直接创建对应的文件夹,业务继续进行!!")
        # parents = True 可以创建多层文件夹   linux mkdir -P x/x/x/x/x
        # exist_ok=True  存在也不报错! 防御性编程
        local_dir_obj.mkdir(parents=True, exist_ok=True)
    # 3.6 return pdf_path_obj , local_dir_obj
    return pdf_path_obj, local_dir_obj


"""
apply_mineru_get_upload_url(pdf_file_name:str) -> tuple[str,str]
        4.1 组装对应的请求头 (token)
        4.2 组长对应的请求体json数据(请求参数)
        4.3 向对应的接口发起post方式请求,并等待[阻塞]获取结果
        4.4 判断http协议网络状态status_code
        4.5 判断业务状态码code
        4.6 获取目标结果batch_id/upload_url地址
        4.7 返回结果即可
"""


def apply_mineru_get_upload_url(pdf_file_name: str) -> tuple[str, str]:
    # https://mineru.net/apiManage/docs
    # 4.1 组装对应的请求头 (token)
    token = infra_config.mineru_config.api_key
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"  # 千万有空格
    }
    # 4.2 组装对应的请求体json数据(请求参数)
    data = {
        # dict ->  requests(json=dict -> json字符串)
        # 请求参数 == 对方服务器决定
        "files": [
            {"name": pdf_file_name}
        ],
        "model_version": MINERU_MODEL_VERSION,
        "extra_formats": ["html"]
        # "callback":"节点地址http://127.0.0.1:8080/xxx/xx"
    }
    # 4.3 向对应的接口发起post方式请求,并等待[阻塞]获取结果
    url = f"{infra_config.mineru_config.base_url}/file-urls/batch"
    response = requests.post(
        url=url,
        headers=header,
        json=data,
        timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS
    )
    # 4.4 判断http协议网络状态status_code
    status_code = response.status_code
    if status_code != 200:
        logger.error(f"向minerU服务器申请解析地址,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")
        raise RuntimeError(
            f"向minerU服务器申请解析地址,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")
    # 4.5 判断业务状态码code
    # response -> 响应数据 -> code
    # response.text
    # response.content
    response_json = response.json()
    code = response_json.get("code", -1)
    if code != 0:
        logger.error(f"向minerU服务器申请解析地址,业务状态码为:{code},请求失败!业务无法继续,提前终止!!")
        raise RuntimeError(f"向minerU服务器申请解析地址,业务状态码为:{code},请求失败!业务无法继续,提前终止!!")
    # 4.6 获取目标结果batch_id/upload_url地址
    json_data = response_json.get("data", {})
    batch_id: str = json_data.get("batch_id")
    upload_file_url: str = json_data.get("file_urls")[0]
    # 4.7 返回结果即可
    return batch_id, upload_file_url


"""
   我申请文件上传地址 -> minerU -> 上传文件地址   [url , batch_id]
   我向地址上传具体文件 -> 上传文件地址 -> put(data=文件数据)
   轮询等待minerU解析解析 -> [ 轮询 ] 查询解析状态  batch_id -> zip_url下载解析结果地址

   minerU获取解析结果:
     方案1: 轮询 batch_id -> 根据batch_id轮询查询即可
     方案2: 接口回调 申请 -> 配置回调接口 -> minerU解析完毕 -> 他主动调用接口 -> 传递解析结果 
           问题1: 接口地址必须是公网地址
           问题2: 异步动作

"""

"""
upload_file_to_url(upload_url地址:str,pdf_path_obj:Path) -> None:
        5.1 读取上传文件的数据pdf_path_obj->字节的数据
        5.2 向指定的地址发起put请求,传递pdf文件数据
        5.3 判断响应状态码,不是200抛出异常! [本次只需要判断http状态码,不需要判断业务code! 本身就是不是minerU业务接口,文件服务器的上传地址]
"""


def upload_file_to_url(upload_url: str, pdf_path_obj: Path) -> None:
    # 5.1 读取上传文件的数据pdf_path_obj->字节的数据
    """
      Path -> 一个路径的对象 / 对象的属性. / 路径对象的一些简单方法 数据读取 判断 校验...
         .name .stem .suffix .parent .parents
         .is_file() .is_dir()  .exists()  .read_text() .read_bytes()  write_text()  write_bytes()
         iterdir() glob() rglob()
    """
    data = pdf_path_obj.read_bytes()
    # 5.2 向指定的地址发起put请求,传递pdf文件数据
    # response = requests.put(url=upload_url,data=data,timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)
    # 5.3 判断响应状态码,不是200抛出异常! [本次只需要判断http状态码,不需要判断业务code! 本身就是不是minerU业务接口,文件服务器的上传地址]
    #  session ->   requests.put 一次请求  1. 复用请求 2.session.trust_env = False 不要给我额外的添加任何请求! 我本次设置了什么,你就给我传递什么?
    with requests.Session() as session:
        session.trust_env = False
        response = session.put(url=upload_url, data=data, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)

    status_code = response.status_code
    if status_code != 200:
        logger.error(f"向:{upload_url}地址上传文件,网络状态失败:{status_code},业务无法继续,提前终止!!")
        raise RuntimeError(f"向:{upload_url}地址上传文件,网络状态失败:{status_code},业务无法继续,提前终止!!")

    # 不需要请求头和传递对应的token呢?
    # 为啥之前需要呢? minerU接口 minerU有访问限制,需要再请求头传递你的token校验我们是否超过了他的限制!!
    # 本次minerU搭建的文件服务器直接发起的请求,没有通过minerU接口!所以不需要传递token!!
    # 文件服务器难道说可以随便传递数据? 只要有个地址就可以传递数据了???
    # 文件服务器 访问可以匿名(不需要认证) 上传文件需要认证 (预签名 地址上携带认证信息(地址权限很高) | 认证后的客户端传递)
    # requests.put(url=upload_url,data=data,timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS) 很大概率文件服务器会拒绝?


"""
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
"""


def poll_mineru_zip_url(batch_id: str) -> str:
    # 6.1 接收常量参数 临时变量接收值 最大轮询时间 / 轮询间隔时间 / 记录起始时间
    max_timeout = MINERU_POLL_TIMEOUT_SECONDS
    interval_time = MINERU_POLL_INTERVAL_SECONDS
    start_time = time.time()  # 时间秒

    url = f"{infra_config.mineru_config.base_url}/extract-results/batch/{batch_id}"
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {infra_config.mineru_config.api_key}"
    }

    # 6.2 死循环 while True:
    while True:
        # 6.2.1 有没有超过最大等待时间 [1~N]
        if time.time() - start_time >= max_timeout:
            logger.error(
                f"轮询获取解析结果时间超时!等待时间为:{time.time() - start_time},最大等待时间:{max_timeout},业务无法继续,提前终止!!")
            raise TimeoutError(
                f"轮询获取解析结果时间超时!等待时间为:{time.time() - start_time},最大等待时间:{max_timeout},业务无法继续,提前终止!!")
        # 6.2.2 向指定的地址请求查询解析状态
        response = requests.get(url, headers=header, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)
        # 6.2.3 判断网络状态码status_code != 200  [判断是否可以给与机会(5xx),可以等待重试 / 其他的也需要抛出异常终止轮询 ]
        status_code = response.status_code
        if status_code != 200:
            # 错误可以重试   5xx [我们是客户端 -> 服务端]
            if 500 <= status_code < 600:
                logger.warning(f"轮询获取解析结果,出现服务器异常,状态码为:{status_code},稍后重试!!")
                time.sleep(interval_time)  # 线程休眠!
                continue
            # 错误不可以重试
            logger.error(
                f"轮询获取解析结果,出现异常,状态码为:{status_code},异常是不可修复和重试,业务无法继续,提前终止!!")
            raise RuntimeError(
                f"轮询获取解析结果,出现异常,状态码为:{status_code},异常是不可修复和重试,业务无法继续,提前终止!!")
        # 6.2.4 判断业务状态码code != 0 [需要抛出异常终止轮询]
        json_data = response.json()
        code = json_data.get("code", -1)
        if code != 0:
            logger.error(
                f"轮询获取解析结果,业务状态出现异常,code为:{code},异常是不可修复和重试,业务无法继续,提前终止!!")
            raise RuntimeError(
                f"轮询获取解析结果,业务状态出现异常,code为:{code},异常是不可修复和重试,业务无法继续,提前终止!!")
        # 判断文件的解析状态state
        result = json_data.get("data", {}).get("extract_result", [])[0]
        state = result.get("state")

        if state == "done":
            # 解析完成了
            full_zip_url: str = result.get("full_zip_url")
            logger.info(f"完成文件内容解析,获取的下载地址为:{full_zip_url}")
            return full_zip_url
        elif state == "failed":
            # 解析失败了
            logger.error(f"文件解析失败,业务无法继续,提前终止!!")
            raise RuntimeError(f"文件解析失败,业务无法继续,提前终止!!")
        else:
            # 正在解析中
            logger.info(f"文件正在解析中,当前状态为:{state},稍后重试!!")
            time.sleep(interval_time)
            continue


"""
download_and_extract_md(zip_file_url:str,pdf不带后缀名的名称上stem:str) -> str:
        7.1 向指定的zip下载地址发起请求(get) 响应字节数据(运行内存)
        7.2 创建一个存储zip数据的文件 output / stem_result.zip
        7.3 将字节数据写到zip的文件中 (write_bytes(data))
        7.4 判断文件地址是否存在 output / stem
        7.5 存在先清空,删除
        7.6 真实创建对应的文件夹  output / stem
        7.7 zip文件解压到对应输出文件夹
        7.8 检查输出文件夹中是否存在md文件 没有 -> 终止业务
        7.9 检查md文件是否叫 stem.md , 是直接返回即可 Path -> str
        7.10 再检查叫不叫full.md -> 重命名 -> 新地址返回
        7.11 终止业务
"""


def download_and_extract_md(zip_file_url: str, local_dir_obj: Path, stem: str) -> str:
    #  7.1 向指定的zip下载地址发起请求(get) 响应字节数据(运行内存)
    response = requests.get(zip_file_url, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)
    status_code = response.status_code
    if status_code != 200:
        logger.error(f"从:{zip_file_url}下载文件重现网络异常,状态码为:{status_code},业务无法继续,提前终止!!")
        raise RuntimeError(f"从:{zip_file_url}下载文件重现网络异常,状态码为:{status_code},业务无法继续,提前终止!!")
    # 7.2 创建一个存储zip数据的文件 output / stem_result.zip
    zip_file_obj: Path = local_dir_obj / f"{stem}_result.zip"
    # 7.3 将字节数据写到zip的文件中 (write_bytes(data))
    data = response.content  # json() -> minerU json字符串  .text  接口 普通字符串 "我爱你中国!"  .content  接口 返回的自己数据 文件
    zip_file_obj.write_bytes(data=data)

    # 7.4 判断文件地址是否存在 output / stem
    zip_file_dir: Path = local_dir_obj / stem
    # 7.5 存在先清空,删除
    if zip_file_dir.is_dir():
        # 清空 本身和内容都清空
        shutil.rmtree(zip_file_dir)  # 递归删除  删除自己内部的文件,删除自己本身
    # 7.6 真实创建对应的文件夹  output / stem
    zip_file_dir.mkdir(parents=True, exist_ok=True)
    # 7.7 zip文件解压到对应输出文件夹
    # 参数1: 要解压的文件 Path对象或者字符串对象
    # 参数2: 要解压到哪个文件夹地址  不要指定解压类型,自动识别
    shutil.unpack_archive(zip_file_obj, zip_file_dir)
    # 参数1: 压缩后的文件名 info
    # 参数2: 压缩后的格式   zip
    # 参数3: 压缩哪个文件夹
    # shutil.make_archive()
    # 7.8 检查输出文件夹中是否存在md文件 没有 -> 终止业务
    # 思路1: 文件夹的文件都拿出来,比较后缀名 List[Path] = Path.iterdir() -> 获取文件夹下的所有文件或者文件夹 [不嵌套获取 3]
    # 思路2: 获取文件夹下指定的文件类型   Path.glob("*.md") -> full.md / r->递归 ** /  glob(*.md) full.md / xx.md
    md_list: list[Path] = list(zip_file_dir.rglob("*.md"))
    # zip_file_dir.glob("*.md")
    if not md_list:
        logger.error(f"已经将文件解压到了{local_dir_obj}文件夹,但是内部没有md文件,业务无继续,提前终止!!")
        raise RuntimeError(f"已经将文件解压到了{local_dir_obj}文件夹,但是内部没有md文件,业务无继续,提前终止!!")
    # 7.9 检查md文件是否叫 stem.md , 是直接返回即可 Path -> str
    for md_file in md_list:
        if md_file.stem == stem:  # 解压的名字直接等于原文件名
            logger.info(f"解压后直接存在原文件名({md_file.name})对应的md文件,无需重命名,直接返回即可!")
            return str(md_file)
    # 7.10 再检查叫不叫full.md -> 重命名 -> 新地址返回
    target_md_obj: Path | None = None
    for md_file in md_list:
        if md_file.stem == "full":
            target_md_obj = md_file
            break
    if target_md_obj:
        # 找到了full.md  写重命名规则
        # full.md / stem.md
        # Path  rename - 剪切  删除原文件 -> 新文件
        # 注意: 返回值才是修改后的地址
        """
         问题: md没了下载的文件中没了,跑到了nodes下面 (node_pdf_to_md所在的文件夹)
         解释: rename(f"hak180使用手册.md") 使用的相对地址,相对的不是原文件,是执行文件所在的文件夹
         解决: 绝对地址  新的目标绝对地址  =  要修改文件的绝对地址对象.with_name(要修改的目标文件名) 修改某个路径的文件名  绝对地址... /full.md  -> 绝对地址... /xxx.md
        """
        #  xxx/xx/xx/烫金机.md  =  xxx/xx/xx/full.md  = 烫金机.md
        new_target_md_obj: Path = target_md_obj.with_name(f"{stem}.md")
        new_md_obj: Path = target_md_obj.rename(new_target_md_obj)
        logger.info(f"已经完成full.md重命名,新的文件地址为:{new_md_obj}~")
        return str(new_md_obj)
    else:
        # 7.11 终止业务
        logger.error(
            f"解压后的文件夹中存在{len(md_list)}个md文件,但是没有叫原文件名{stem}/full.md文件,也无法确定哪个文件,业务无法继续,提前终止!!")
        raise RuntimeError(
            f"解压后的文件夹中存在{len(md_list)}个md文件,但是没有叫原文件名{stem}/full.md文件,也无法确定哪个文件,业务无法继续,提前终止!!")


def parse_pdf_to_markdown(state: ImportGraphState) -> ImportGraphState:
    # 1. 进行参数合理性校验
    pdf_path_obj, local_dir_obj = validates_pdf_paths(state)
    # 2. 向minerU申请文件上传地址和batch_id
    batch_id, upload_file_url = apply_mineru_get_upload_url(pdf_path_obj.name)
    # 3. 向指定的文件地址(预签名地址)上传文件数据
    upload_file_to_url(upload_file_url, pdf_path_obj)
    # 4. 轮询获取解析结果
    full_zip_url: str = poll_mineru_zip_url(batch_id)
    # 5. 下载并解压和重命名文件
    md_path: str = download_and_extract_md(full_zip_url, local_dir_obj, pdf_path_obj.stem)
    # 6. 更新state md_path
    state['md_path'] = md_path
    return state