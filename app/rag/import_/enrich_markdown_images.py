import base64
import re
from mimetypes import guess_type
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.infra.llm.providers import llm_provider
from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import IMAGE_CONTEXT_CHAR_LENGTH, SUPPORTED_IMAGE_EXTENSIONS
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger


"""
1. 获取核心参数和数据校验
目标: state 获取: md_path_obj images_path_obj md_content
validates_and_get_data(state:ImportGraphState) -> tuple[str,Path,Path]
1.1 获取md_path参数从state
1.2 md_path的非空校验
1.3 转成md_path_obj Path对象,做存在性校验! is_file()
1.4 使用md_path对象读取md_content,更新state
1.5 md_path_obj可以获取images path地址
1.6 顺序返回 return md_content,..
"""
def validates_and_get_data(state:ImportGraphState) -> tuple[str,Path,Path]:
    # 1.1 获取md_path参数从state
    md_path:str = state.get("md_path")
    # 1.2 md_path的非空校验
    if not md_path:
        logger.error(f"md_path内容为空,业务无法继续,提前终止!")
        raise ValueError(f"md_path内容为空,业务无法继续,提前终止!")
    # 1.3 转成md_path_obj Path对象,做存在性校验! is_file()
    md_path_obj:Path = Path(md_path)
    if not md_path_obj.is_file():
        logger.error(f"md_path地址有值:{md_path},但是没有对应的文件,业务无法继续,提前终止!")
        raise FileNotFoundError(f"md_path地址有值:{md_path},但是没有对应的文件,业务无法继续,提前终止!")
    # 1.4 使用md_path对象读取md_content,更新state
    md_content:str = md_path_obj.read_text(encoding="utf-8")
    state["md_content"] = md_content
    # 1.5 md_path_obj可以获取images path地址
    images_path_obj:Path = md_path_obj.parent / "images"
    # 1.6 顺序返回 return md_content,..
    return md_content,md_path_obj,images_path_obj

"""
2. 读取md中使用图片的信息 上下文和图片的本身路径
        从images中获取图片地址(Path),使用正则在md_content中查找和匹配,匹配到以后,获取上下文信息
        传递: images_path_obj  md_content  获取: 图片名 Path.name  图片Path对象  图片上文 图片下文   [(图片名字str,图片Path对象,(上文,下文))]
        scan_images_info(images_path_obj:Path,md_content:str) -> list[tuple[str,Path,tuple[str,str]]]
        2.1 获取images下的所有图片Path对象 [列表/生成器]
        2.2 循环每一张图片对象
            2.2.1 定义这个图片的正则规则
            2.2.2 使用正则到md_content中进行匹配
            2.2.3 检查是否匹配 Match是否为空
            2.2.4 获取对应上下信息
            2.2.5 组装当前的数据元组 (图片名字str,图片Path对象,(上文,下文)) 添加到大的列表
        2.3 返回列表数据
"""
def scan_images_info(images_path_obj:Path,md_content:str) -> list[tuple[str,Path,tuple[str,str]]]:
    # 2.1 获取images下的所有图片Path对象 [列表/生成器]
    # images_path_obj   iterdir() | glob("*.jpg")/rglob("规则")
    generator =  images_path_obj.iterdir()
    images_info_list:list[tuple[str,Path,tuple[str,str]]] = []
    # 2.2 循环每一张图片对象
    for image_file_obj in  generator:
        # 是不是图片检查
        if image_file_obj.suffix not in SUPPORTED_IMAGE_EXTENSIONS:
            logger.debug(f"{image_file_obj.name}不是图片,跳过,进行下一张处理!")
            continue
        # 2.2.1 定义这个图片的正则规则
        image_name:str = image_file_obj.name
        # 参数1: 定义的正则,每次都不同,没有必要提前编译
        # 参数2: 正则生效的字符串
        match =  re.search(r"\!\[.*?\]\(.*?"+re.escape(image_name)+".*?\)",md_content)
        # 2.2.3 检查是否匹配 Match是否为空
        if not match:
            logger.debug(f"{image_name}没有在md_content被使用,跳过,进行下一张处理!")
            continue
        # 2.2.4 获取对应上下信息
        start = match.start()
        end   = match.end()
        # xxx ! []( ) xxxx
        # IMAGE_CONTEXT_CHAR_LENGTH
        # [)
        # str[,start ! 不要] -> 字符串截取
        # [1 负值 0 最小值 ,2 没问题]
        pre_context:str  = md_content[max(start-IMAGE_CONTEXT_CHAR_LENGTH,0): start]
        post_context:str = md_content[end + 1: min(end+IMAGE_CONTEXT_CHAR_LENGTH,len(md_content))]
        images_info_list.append(
            (
                image_name,
                image_file_obj,
                (
                    pre_context,
                    post_context
                )
            )
        )
    logger.info(f"已经完成了{len(images_info_list)}张图片内容的匹配!")
    return images_info_list

"""
summary_image_info(image_info:list[tuple[str,Path,tuple[str,str]]],root_folfer:str) -> dict[str,str]
    3.1 数据准备工作 初始化一个视觉模型对象 | 定义一个接收数据的字典
    3.2 循环处理每一张图片    for str,Path,context in  list[tuple[str,Path,tuple[str,str]]]
        3.3 封装模型提示词信息 
        3.4 封装调用链: 直接 model.invoke | 调用链 提示词 | 模型 | 解析器 OutParser() 
        3.5 使用调用链进行调用和获取结果
        3.6 添加到字典中 {image_name,image_summary}
    3.7 跳出循环->返回整体字典
"""

def summary_image_info(image_info:list[tuple[str,Path,tuple[str,str]]],root_folder:str) -> dict[str,str]:
    # 3.1 数据准备工作 初始化一个视觉模型对象 | 定义一个接收数据的字典
    images_summary:dict[str,str] = {}
    vision_model = llm_provider.vision_chat()
    # 3.2 环处理每一张图片    for str,Path,context in  list[tuple[str,Path,tuple[str,str]]]
    for image_name,image_path_obj,image_context in image_info:
        # 3.3 封装模型提示词信息
        # 3.3.1 图片的描述 包裹上下文信息一段提示词
        image_des :str   = load_prompt("image_summary",image_content=image_context,root_folder=root_folder)
        image_type:str   = guess_type(image_name)[0]  #(类型,None)
        image_base64:str = base64.b64encode(image_path_obj.read_bytes()).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": image_des},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_type};base64,{image_base64}"},
                },
            ]
        )
        # 3.4 封装调用链: 直接 model.invoke | 调用链 提示词 | 模型 | 解析器 OutParser()
        #chains = 提示词 | 模型 | 解析器
        chains = vision_model | StrOutputParser()
        # 3.5 使用调用链进行调用和获取结果
        summary:str = chains.invoke([message])
        # model.invoke([]) -> response -> response . content -> 字符串
        # chains = vision_model | JSONOutputParser()
        # model.invoke([]) -> response -> response . content -> 字符串 -> json.loads(字符串) -> dict
        # 3.6 添加到字典中 {image_name,image_summary}
        images_summary[image_name] = summary
        logger.debug(f"图片:{image_name},已经通过视觉模型进行意图识别,结果为:{summary}")
    logger.info(f"已经完成{root_folder}文件夹中的所有图片内容总结,总结图的内容对数为:{len(images_summary)}")
    return images_summary







def enrich_markdown_images(state: ImportGraphState) -> ImportGraphState:
    """
    Markdown 图片增强服务：
    1. 扫描 Markdown 中的图片
    2. 调用多模态模型生成图片说明
    3. 上传图片到 MinIO
    4. 替换 Markdown 图片地址并回写 md_content
    """
    # 1. 获取参数并且校验
    md_content, md_path_obj, images_path_obj = validates_and_get_data(state)
    # 2. 调用方法进行图片信息识别
    images_info_list: list[tuple[str, Path, tuple[str, str]]] = scan_images_info(images_path_obj, md_content)
    return state