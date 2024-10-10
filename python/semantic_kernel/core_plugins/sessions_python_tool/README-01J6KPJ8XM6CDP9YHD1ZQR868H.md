---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:52:35Z
---

# Getting Started with the Sessions Python Plugin

## Setup

Please follow the [Azure Container Apps Documentation](ht****************************************************************************er) to get started.

## Configuring the Python Plugin

To successfully use the Python Plugin in Semantic Kernel, you must install the Poetry `azure` extras by running `poetry install -E azure`.

Next, as an environment variable or in the .env file, add the `poolManagementEndpoint` value from above to the variable `ACA_POOL_MANAGEMENT_ENDPOINT`. The `poolManagementEndpoint` should look something like:

```html {"id":"01J6KPQPB3JXBW56YBJ6P489J4"}
ht***************************************ns/{{subscriptionId}}/resourceGroups/{{resourceGroup}}/sessionPools/{{sessionPool}}/python/execute
```

It is possible to add the code interpreter plugin as follows:

```python {"id":"01J6KPQPB3JXBW56YBJ9JYMTVB"}
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

```python {"id":"01J6KPQPB3JXBW56YBJDHT7FXV"}
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
