import re


# 正则 一种字符串匹配规则 使用正则 对目标字符进行: 判断  [ 搜索  ] 替换...

""" 
  1. 定义正则 
     方案1: 提前编译正则,先定义好,反复使用: 一种正则规则多次使用!! 编译后的正则对象 =  re.compile("正则规则...")
     方案2: 不提前编译正则,在使用的时候提供正则
  2. 使用正则匹配
     方案1的使用: 符合的内容 = 编译后的正则对象.search("内容")
     方案2的使用: 符合的内容 = re.search("正则规则","内容")
"""

md_content = "这里有demo(1).png一张图 ![示意图](images/demo(1).png) 再来一张 ![图片](images/demo(1).png)"

image_name = "demo(1).png"
new_image_name = re.escape(image_name)
print(new_image_name)


# 编译正则（不变） 正则中有两类字符 [元字符 . * ? ! [a-z] {} ] 特殊含义的字符串 __ [ 字面字符 a b c d  png ]
# r = raw 原始字符串 python 不要转移 \n 没有r换行 r \n
# 元字符   -> 特殊含义的字符串 默认表达的不是本身含义
# 字面字符 -> 没有特殊含义,表达的本身的含义
# 问题: 把一些元字符,想使用它本身的含义   ! -> 本身的含义 [  ] -> 本身的含义  ( ) -> 本身的含义 元字符
# 解决: 元字符本身的含义!  \! -> 本身的含义
rep = re.compile(r"\!\[.*?\]\(.*?"+new_image_name+".*?\)")

"""
 search  -> 找到第一个匹配项 -> Match .group()  -> 匹配内容 .start() 起始坐标 .end() 结束坐标
 match   -> 从头开始匹配,找到对应的匹配对象 -> Match -> None
 finditer-> 找到所有匹配项  -> List[Match] -> 2
 
       匹配项 (![示意图](images/demo(1).png) | 坐标信息等等)
 --------------------
 findall -> 找到所有匹配内容 -> List[str]
"""

# 1. search：全文找【第一个】匹配 → 返回 match 对象
# re.search(r"正则",md_content)
match_obj = rep.search(md_content)
print("1. search 结果：", match_obj.group() if match_obj else "未找到")
print(f"1. search 坐标：start = {match_obj.start()} , end = {match_obj.end()}")

# 2. match：只从【开头】匹配 → 这里开头不是图片语法，必找不到
match_first = rep.match(md_content)
print("2. match 结果：", "找到" if match_first else "未找到（只匹配开头）")

# 3. findall：找【所有】匹配 → 返回字符串列表
all_list = rep.findall(md_content)
print("3. findall 列表：", all_list)

# 4. finditer：找【所有】匹配 → 返回 match 对象（你要的“search 匹配所有”）
print("4. finditer 遍历所有：")
for m in rep.finditer(md_content):
    print("  - 内容：", m.group(), " | 位置：", m.span())

# () 和 ?  贪婪匹配
text = "A123B456B"
# 1. 用 .*  → 贪婪（吃到最后）
print(re.findall(r"A(.*)B", text))  # 输出：123B456
# 2. 用 .*? → 非贪婪（找到第一个就停）
print(re.findall(r"A(.*?)B", text)) # 输出：123