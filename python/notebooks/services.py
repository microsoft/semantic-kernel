from enum import Enum

class Service(Enum):
    OpenAI = 'openai'
    AzureOpenAI = 'azureopenai'
    HuggingFace = 'huggingface'
