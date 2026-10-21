import time
from http.client import responses
from pathlib import Path

import requests

from app.infra.config.providers import infra_config
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import MINERU_MODEL_VERSION, MINERU_DOWNLOAD_TIMEOUT_SECONDS, MINERU_POLL_TIMEOUT_SECONDS, \
    MINERU_POLL_INTERVAL_SECONDS
from app.shared.runtime.logger import logger, PROJECT_ROOT


"""
 validates_pdf_paths(state:ImportGraphState) -> tuple[Path,Path]
        3.1 从state中获取pdf_path和local_dir地址 -> str
        3.2 非空校验 如果pdf_path为空 error / raise  | 如果 local_dir为空  给与默认值 项目根地址 / "output" -> state['local_dir'] = local_dir
        3.3 将pdf_path和local_dir转成Path对象,方便后续操作 -> Path
        3.4 检查pdf_path_obj是否真实存在 exists() | is_file() 有效[存在]的文件  不是有效文件 error raise
        3.5 检查local_dir_obj是否是真实存在  is_dir() ! 不是有效 mk_dir()
        3.6 return pdf_path_obj , local_dir_obj
"""
def validates_pdf_paths(state:ImportGraphState) -> tuple[Path,Path]:
    # 3.1 从state中获取pdf_path和local_dir地址 -> str
    pdf_path:str  = state.get("pdf_path")
    local_dir:str = state.get("local_dir")
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
    pdf_path_obj:Path  = Path(pdf_path)
    local_dir_obj:Path = Path(local_dir)
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
        local_dir_obj.mkdir(parents=True,exist_ok=True)
    # 3.6 return pdf_path_obj , local_dir_obj
    return pdf_path_obj,local_dir_obj

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
def apply_mineru_get_upload_url(pdf_file_name:str) -> tuple[str,str]:
    # https://mineru.net/apiManage/docs
    # 4.1 组装对应的请求头 (token)
    token = infra_config.mineru_config.api_key
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"   # 千万有空格
    }
    # 4.2 组装对应的请求体json数据(请求参数)
    data = {
        # dict ->  requests(json=dict -> json字符串)
        # 请求参数 == 对方服务器决定
        "files":[
            {"name":pdf_file_name}
        ],
        "model_version":MINERU_MODEL_VERSION,
        "extra_formats":["html"]
        #"callback":"节点地址http://127.0.0.1:8080/xxx/xx"
    }
    # 4.3 向对应的接口发起post方式请求,并等待[阻塞]获取结果
    url = f"{infra_config.mineru_config.base_url}/file-urls/batch"
    response = requests.post(
        url = url,
        headers = header ,
        json = data ,
        timeout= MINERU_DOWNLOAD_TIMEOUT_SECONDS
    )
    # 4.4 判断http协议网络状态status_code
    status_code = response.status_code
    if status_code != 200:
        logger.error(f"向minerU服务器申请解析地址,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")
        raise RuntimeError(f"向minerU服务器申请解析地址,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")
    # 4.5 判断业务状态码code
    # response -> 响应数据 -> code
    # response.text
    # response.content
    response_json = response.json()
    code = response_json.get("code",-1)
    if code != 0:
        logger.error(f"向minerU服务器申请解析地址,业务状态码为:{code},请求失败!业务无法继续,提前终止!!")
        raise RuntimeError(f"向minerU服务器申请解析地址,业务状态码为:{code},请求失败!业务无法继续,提前终止!!")
    # 4.6 获取目标结果batch_id/upload_url地址
    json_data = response_json.get("data", {})
    batch_id:str =  json_data.get("batch_id")
    upload_file_url:str = json_data.get("file_urls")[0]
    # 4.7 返回结果即可
    return batch_id,upload_file_url


"""
upload_file_to_url(upload_url地址:str,pdf_path_obj:Path) -> None:
        5.1 读取上传文件的数据pdf_path_obj->字节的数据
        5.2 向指定的地址发起put请求,传递pdf文件数据
        5.3 判断响应状态码,不是200抛出异常! [本次只需要判断http状态码,不需要判断业务code! 本身就是不是minerU业务接口,文件服务器的上传地址]
"""

def upload_file_to_url(upload_url:str,pdf_path_obj:Path)-> None:
    # 5.1 读取上传文件的数据pdf_path_obj->字节的数据
    data = pdf_path_obj.read_bytes()

    # 5.2向指定的地址发起put请求, 传递pdf文件数据
    # response = requests.put(url=upload_url,data=data,timeout= MINERU_DOWNLOAD_TIMEOUT_SECONDS)

    with requests.session() as session:
        session.trust_env = False
        response = session.put(url=upload_url,data=data,timeout= MINERU_DOWNLOAD_TIMEOUT_SECONDS)

    #5.3 判断响应状态码,不是200抛出异常! [本次只需要判断http状态码,不需要判断业务code! 本身就是不是minerU业务接口,文件服务器的上传地址]
    status_code = response.status_code
    if status_code != 200:
        logger.error(f"向minerU服务器上传文件,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")
        raise RuntimeError(f"向minerU服务器上传文件,但是出现网络异常!状态码为:{status_code},业务无法继续,提前终止!!")


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
    start_time = time.time()

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
                f"轮询获取解析结果时间超时！等待时间为：{time.time() - start_time},最大等待时间：{max_timeout}，业务无法继续，提前终止！！")
            raise TimeoutError(
                f"轮询获取解析结果时间超时！等待时间为：{time.time() - start_time},最大等待时间：{max_timeout}，业务无法继续，提前终止！！")

        # 6.2.2 向指定的地址请求查询解析状态
        response = requests.get(url, headers=header, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)
        # 6.2.3 判断网络状态码status_code != 200  [判断是否可以给与机会(5xx),可以等待重试 / 其他的也需要抛出异常终止轮询 ]
        if response.status_code != 200:
            if response.status_code >= 500:
                logger.warning(
                    f"向minerU服务器查询解析状态,但是出现网络异常!状态码为:{response.status_code},业务可以继续,等待重试!!")
                time.sleep(interval_time)
                continue
            logger.error(
                f"向minerU服务器查询解析状态,但是出现网络异常!状态码为:{response.status_code},业务无法继续,提前终止!!")
            raise RuntimeError(
                f"向minerU服务器查询解析状态,但是出现网络异常!状态码为:{response.status_code},业务无法继续,提前终止!!")

        # 6.2.4 判断业务状态码code != 0 [需要抛出异常终止轮询]
        json_data = response.json()
        code = json_data.get("code")
        if code != 0:
            logger.error(f"向minerU服务器查询解析状态,但是出现业务异常!状态码为:{code},业务无法继续,提前终止!!")
            raise RuntimeError(f"向minerU服务器查询解析状态,但是出现业务异常!状态码为:{code},业务无法继续,提前终止!!")

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


def parse_pdf_to_markdown(state: ImportGraphState) -> ImportGraphState:
    """
    PDF 解析服务：
    1. 调用 MinerU
    2. 下载并解压解析结果
    3. 获取 Markdown 路径和正文内容
    4. 回写 md_path / md_content / local_dir
    """
    # 1. 进行参数合理性校验
    pdf_path_obj,local_dir_obj = validates_pdf_paths(state)

    # 2. 向minerU申请文件上传地址和batch_id
    batch_id,upload_file_url = apply_mineru_get_upload_url(pdf_path_obj.name)

    # 3. 向指定的文件地址(预签名地址)上传文件数据
    upload_file_to_url(upload_file_url,pdf_path_obj)
    # 4. 轮询获取解析结果
    full_zip_url: str = poll_mineru_zip_url(batch_id)

    return state
