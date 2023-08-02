import asyncio
import logging

import semantic_kernel as sk
from semantic_kernel import ContextVariables, Kernel
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from semantic_kernel.connectors.openapi import register_openapi_skill

# Example usage
chatgpt_retrieval_plugin = {
    "openapi": "C:/Users/markkarle/localworkspace/chatgpt-retrieval-plugin/local_server/openapi.yaml",
    "request_body": {
        "queries": [
            {
                "query": "string",
                "filter": {
                    "document_id": "string",
                    "source": "email",
                    "source_id": "string",
                    "author": "string",
                    "start_date": "string",
                    "end_date": "string",
                },
                "top_k": 3,
            }
        ]
    },
    "operation_id": "query_query_post",
}

sk_python_flask = {
    "openapi": "C:/Users/markkarle/localworkspace/mkarle/semantic-kernel-starters/sk-python-flask-chatgpt-plugin/openapi.yaml",
    "path_params": {"skill_name": "FunSkill", "function_name": "Joke"},
    "request_body": {"input": "dinosaurs"},
    "operation_id": "executeFunction",
}
google_chatgpt_plugin = {
    "openapi": "C:/Users/markkarle/localworkspace/mkarle/google-chatgpt-plugin/.well-known/openapi.yaml",
    "query_params": {"q": "dinosaurs"},
    "operation_id": "searchGet",
}

todo_plugin_add = {
    "openapi": "C:/Users/markkarle/localworkspace/chat-todo-plugin/openapi.yaml",
    "path_params": {"username": "markkarle"},
    "request_body": {"todo": "finish this"},
    "operation_id": "addTodo",
}

todo_plugin_get = {
    "openapi": "C:/Users/markkarle/localworkspace/chat-todo-plugin/openapi.yaml",
    "path_params": {"username": "markkarle"},
    "operation_id": "getTodos",
}

todo_plugin_delete = {
    "openapi": "C:/Users/markkarle/localworkspace/chat-todo-plugin/openapi.yaml",
    "path_params": {"username": "markkarle"},
    "request_body": {"todo_idx": 0},
    "operation_id": "deleteTodo",
}


plugin = sk_python_flask

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

kernel = Kernel(log=logger)
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
kernel.add_text_completion_service(
    "dv", AzureTextCompletion(deployment, endpoint, api_key)
)

skill = register_openapi_skill(
    kernel=kernel, skill_name="test", openapi_document=plugin["openapi"]
)
context_variables = ContextVariables(variables=plugin)
result = asyncio.run(
    skill[plugin["operation_id"]].invoke_async(variables=context_variables)
)
print(result)
