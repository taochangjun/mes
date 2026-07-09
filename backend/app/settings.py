from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    # 显式定义所有需要的字段，并赋予合适的类型和默认值
    deepseek_api_key: str = ""
    deepseek_base_url: str = ""
    deepseek_base_url_anthropic: str = ""  # 新增
    deepseek_model_flash: str = "deepseek-v4-flash"  # 新增，可设置默认值
    deepseek_model_pro: str = "deepseek-v4-pro"  # 新增
    deepseek_models: str = ""  # 新增，注意类型，看起来是列表
    # 留空则 SOP 检索使用关键词匹配；配置后启用 embedding 向量检索
    embedding_model: str = ""

    # 指定要加载的 .env 文件
    _BACKEND_DIR = Path(__file__).resolve().parent.parent
    model_config = SettingsConfigDict(env_file=_BACKEND_DIR/"config"/".env",
                                      env_file_encoding="utf-8")


@lru_cache()
def get_settings():
    return Settings()


if __name__ == '__main__':
    print(get_settings())