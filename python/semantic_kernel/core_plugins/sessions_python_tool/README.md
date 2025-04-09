# Getting Started with the Sessions Python Plugin

## Setup

Please follow the [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter) to get started.

## Configuring the Python Plugin

To successfully use the Python Plugin in Semantic Kernel, you must install the `azure` extras by running `uv sync --extra azure` or `pip install semantic-kernel[azure]`.

Next, as an environment variable or in the .env file, add the `poolManagementEndpoint` value from above to the variable `ACA_POOL_MANAGEMENT_ENDPOINT`. The `poolManagementEndpoint` should look something like:

```html
https://eastus.acasessions.io/subscriptions/{{subscriptionId}}/resourceGroups/{{resourceGroup}}/sessionPools/{{sessionPool}}/python/execute
```

You can also provide the the `ACA_TOKEN_ENDPOINT` if you want to override the default value of `https://acasessions.io/.default`. If this token endpoint doesn't need to be overridden, then it is
not necessary to include this as an environment variable, in the .env file, or via the plugin's constructor. Please follow the [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter) to review the proper role required to authenticate with the `DefaultAzureCredential`.

Next, let's move on to implementing the plugin in code. It is possible to add the code interpreter plugin as follows:

```python
kernel = Kernel()

service_id = "azure_oai"
chat_service = AzureChatCompletion(
    service_id=service_id, **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
)
kernel.add_service(chat_service)

python_code_interpreter = SessionsPythonTool(
    auth_callback=auth_callback
)

sessions_tool = kernel.add_plugin(python_code_interpreter, "PythonCodeInterpreter")

code = "import json\n\ndef add_numbers(a, b):\n    return a + b\n\nargs = '{\"a\": 1, \"b\": 1}'\nargs_dict = json.loads(args)\nprint(add_numbers(args_dict['a'], args_dict['b']))"
result = await kernel.invoke(sessions_tool["execute_code"], code=code)

print(result)
```

Instead of hard-coding a well-formatted Python code string, you may use automatic function calling inside of SK and allow the model to form the Python and call the plugin.

The authentication callback must return a valid token for the session pool. One possible way of doing this with a `DefaultAzureCredential` is as follows:

```python
async def auth_callback() -> str:
    """Auth callback for the SessionsPythonTool.
    This is a sample auth callback that shows how to use Azure's DefaultAzureCredential
    to get an access token.
    """
    global auth_token
    current_utc_timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    if not auth_token or auth_token.expires_on < current_utc_timestamp:
        credential = DefaultAzureCredential()

        try:
            auth_token = credential.get_token(ACA_TOKEN_ENDPOINT)
        except ClientAuthenticationError as cae:
            err_messages = getattr(cae, "messages", [])
            raise FunctionExecutionException(
                f"Failed to retrieve the client auth token with messages: {' '.join(err_messages)}"
            ) from cae

    return auth_token.token
```

Currently, there are two concept examples that show this plugin in more detail:

- [Plugin example](../../../samples/concepts/plugins/azure_python_code_interpreter.py): shows the basic usage of calling the code execute function on the plugin.
- [Function Calling example](../../../samples/concepts/auto_function_calling/azure_python_code_interpreter_function_calling.py): shows a simple chat application that leverages the Python code interpreter plugin for function calling.
