import os
from dataclasses import dataclass
from typing import Union
from dotenv import load_dotenv

load_dotenv()

@dataclass
class OpenAILLMConfig:
    """
    A data class to store configuration details for OpenAI models.

    Attributes:
        model_name (str): The name of the OpenAI model to use.
        openai_api_key (str): The API key for authenticating with the OpenAI service.
    """
    model_name: str
    openai_api_key: str


@dataclass
class AzureOpenAILLMConfig:
    """
    A data class to store configuration details for Azure OpenAI deployment.

    Attributes:
        deployment_name (str): The name of the deployment.
        model_name (str): The name of the OpenAI model to use.
        azure_endpoint (str): The endpoint URL for the Azure OpenAI service.
        openai_api_version (str): The API version to use with the Azure OpenAI service.
        openai_api_key (str): The API key for authenticating with the Azure OpenAI service.
    """
    deployment_name: str
    model_name: str
    azure_endpoint: str
    openai_api_version: str
    openai_api_key: str


@dataclass
class ZaiLLMConfig:
    """
    A data class to store configuration details for Zhipu AI models.

    Attributes:
        model_name (str): The name of the Zhipu AI model to use (e.g., "glm-4.7").
        zhipuai_api_key (str): The API key for authenticating with Zhipu AI service.
    """
    model_name: str
    zhipuai_api_key: str


@dataclass
class RequestyLLMConfig:
    """
    A data class to store configuration details for Requesty models.

    Attributes:
        model_name (str): The name of the model to use (e.g., "deepseek/deepseek-chat").
        req_api_key (str): The API key for authenticating with Requesty service.
        base_url (str): The base URL for Requesty API.
    """
    model_name: str
    req_api_key: str
    base_url: str = "https://router.requesty.ai/v1"


LLMConfig = Union[OpenAILLMConfig, AzureOpenAILLMConfig, ZaiLLMConfig, RequestyLLMConfig]


# Azure LLM configuration map
azure_llm_config_map = {
    "gpt-4o": AzureOpenAILLMConfig(
        deployment_name="gpt-4o",
        model_name="gpt-4o",
        azure_endpoint=os.getenv("AZURE_ENDPOINT_GPT4O"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY_GPT4O"),
    ),
    "gpt-4.1": AzureOpenAILLMConfig(
        deployment_name="gpt-4.1",
        model_name="gpt-4.1",
        azure_endpoint=os.getenv("AZURE_ENDPOINT_GPT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
}

# Azure Embedding configuration map
azure_embedding_config_map = {
    "embedding-3-large": AzureOpenAILLMConfig(
        deployment_name="text-embedding-3-large",
        model_name="text-embedding-3-large",
        azure_endpoint=os.getenv("AZURE_ENDPOINT_EMBEDDING_3"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION_EMBEDDING_3"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING_3_LARGE"),
    )
}

# OpenAI config map
llm_config_map = {
    "gpt-4o": OpenAILLMConfig(
        model_name="gpt-4o",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
    "gpt-4.1": OpenAILLMConfig(
        model_name="gpt-4.1",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
}

# Zhipu AI config map
zai_llm_config_map = {
    "glm-4.5": ZaiLLMConfig(
        model_name="glm-4.5",
        zhipuai_api_key=os.getenv("OPENAI_API_KEY"),
    )
}

# Requesty config map
requesty_llm_config_map = {
    "deepseek-chat": RequestyLLMConfig(
        model_name="deepseek/deepseek-chat",
        req_api_key=os.getenv("REQ_API_KEY"),
    )
}
