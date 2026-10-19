from dataclasses import dataclass, field

from app.shared.config.embedding_config import embedding_config, EmbeddingConfig
from app.shared.config.lm_config import lm_config, LLMConfig
from app.shared.config.bailian_mcp_config import mcp_config,McpConfig
from app.shared.config.reranker_config import reranker_config, RerankerConfig
from app.shared.config.milvus_config import milvus_config, MilvusConfig
from app.shared.config.mineru_config import mineru_config, MinerUConfig
from app.shared.config.minio_config import minio_config, MinIOConfig
from app.shared.config.settings_config import settings, AppSettings


def embedding_factory():
    return


@dataclass
class InfraConfig:
    embedding_config:EmbeddingConfig = field(default_factory=lambda: embedding_config)
    lm_config:LLMConfig = field(default_factory=lambda:lm_config)
    mcp_config:McpConfig = field(default_factory=lambda:mcp_config)
    milvus_config:MilvusConfig = field(default_factory=lambda:milvus_config)
    mineru_config:MinerUConfig = field(default_factory=lambda:mineru_config)
    minio_config:MinIOConfig = field(default_factory=lambda:minio_config)
    reranker_config: RerankerConfig = field(default_factory=lambda:reranker_config)
    settings:AppSettings = field(default_factory=lambda:settings)

infra_config = InfraConfig()

# ValueError: mutable default <class ('app.shared.config.embedding_config'
#                                     '.EmbeddingConfig')> for field embedding_config
# is not allowed: use default_factory


# @dataclass / pydantic BaseModel -> 直接给对象的属性默认值 -> 默认值 引用类型 对象 dict list -> 报错 is not allowed: use default_factory
# 原因: 多个属性指向同一个对象,修改以后互相影响不安全!
# 解决: 1. 自己创建一个新的对象 copy  new()  2. 绕开 default_factory = 没有参数函数 期望的返回新的对象 实时不检查 lambda [没有参数] : 对象

# 原因: 属性的默认值是对象 embedding_config 对象是一个引用数据类型!!
# [影响我们] infra_config. embedding_config [修改了]  => 配置对象 <= [修改了] embedding_config.embedding_config.py [影响对方]

# 解决1: import copy copy.deep_copy() -> 全新的对象
# 解决2: field(default_factory= embedding_factory()函数->创建一个'新对象')  事实上,他是提供了格式,并不会真的监督!





