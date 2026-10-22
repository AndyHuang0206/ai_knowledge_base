from app.shared.model.lm_utils import get_llm_client
from app.infra.config.providers import infra_config

class LLMProvider():
    # 大语言模型
    def chat(self, model: str | None = None, json_model: bool = False):
        return get_llm_client(model=model, json_mode=json_model)

    def vision_chat(self,model:str|None = None):
        if not model:
            model= infra_config.lm.config.lv_model
        return get_llm_client(model=model,json_mode=False)
    # ------------ 后续修改扩展 ----------
    # 嵌入式模型

    # 重排序模型

llm_provider = LLMProvider()
