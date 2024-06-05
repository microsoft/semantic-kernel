# Copyright (c) Microsoft. All rights reserved.


# @pytest.mark.asyncio
# async def test_azure_e2e_chat_completion_with_plugin(setup_tldr_function_for_oai_models):
#     kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

#     # Configure LLM service
#     kernel.add_service(
#         sk_oai.AzureChatCompletion(
#             service_id="chat",
#         ),
#     )

#     exec_settings = PromptExecutionSettings(
#         service_id="chat", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
#     )

#     prompt_template_config = PromptTemplateConfig(
#         template=prompt, description="Write a short story.", execution_settings=exec_settings
#     )

#     # Create the semantic function
#     kernel.add_function(function_name="tldr", plugin_name="plugin", prompt_template_config=prompt_template_config)

#     arguments = KernelArguments(input=text_to_summarize)

#     summary = await retry(lambda: kernel.invoke(function_name="tldr", plugin_name="plugin", arguments=arguments))
#     output = str(summary).strip()
#     print(f"TLDR using input string: '{output}'")
#     assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
#     assert len(output) < 100


# @pytest.mark.asyncio
# async def test_azure_e2e_chat_completion_with_plugin_and_provided_client(setup_tldr_function_for_oai_models):
#     kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

#     azure_openai_settings = AzureOpenAISettings.create()
#     endpoint = azure_openai_settings.endpoint
#     deployment_name = azure_openai_settings.chat_deployment_name
#     api_key = azure_openai_settings.api_key.get_secret_value()
#     api_version = azure_openai_settings.api_version

#     client = AsyncAzureOpenAI(
#         azure_endpoint=endpoint,
#         azure_deployment=deployment_name,
#         api_key=api_key,
#         api_version=api_version,
#         default_headers={"Test-User-X-ID": "test"},
#     )

#     # Configure LLM service
#     kernel.add_service(sk_oai.AzureChatCompletion(service_id="chat_completion", async_client=client))

#     exec_settings = PromptExecutionSettings(
#         service_id="chat_completion",
#         extension_data={
#             "max_tokens": 200,
#             "temperature": 0,
#             "top_p": 0.5,
#         },
#     )

#     # Create the semantic function
#     kernel.add_function(
#         function_name="tldr",
#         plugin_name="plugin",
#         prompt=prompt,
#         description="Write a short story.",
#         prompt_execution_settings=exec_settings,
#     )

#     arguments = KernelArguments(input=text_to_summarize)

#     summary = await retry(lambda: kernel.invoke(function_name="tldr", plugin_name="plugin", arguments=arguments))
#     output = str(summary).strip()
#     print(f"TLDR using input string: '{output}'")
#     assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
#     assert len(output) < 100


# @pytest.mark.asyncio
# async def test_azure_oai_chat_service_with_tool_call(kernel: Kernel):
#     azure_openai_settings = AzureOpenAISettings.create()
#     endpoint = azure_openai_settings.endpoint
#     deployment_name = azure_openai_settings.chat_deployment_name
#     api_key = azure_openai_settings.api_key.get_secret_value()
#     api_version = azure_openai_settings.api_version

#     client = AsyncAzureOpenAI(
#         azure_endpoint=endpoint,
#         azure_deployment=deployment_name,
#         api_key=api_key,
#         api_version=api_version,
#         default_headers={"Test-User-X-ID": "test"},
#     )

#     # Configure LLM service
#     kernel.add_service(
#         sk_oai.AzureChatCompletion(
#             service_id="chat_completion",
#             async_client=client,
#         ),
#     )

#     kernel.add_plugin(MathPlugin(), plugin_name="math")

#     execution_settings = AzureChatPromptExecutionSettings(
#         service_id="chat_completion",
#         max_tokens=2000,
#         temperature=0.7,
#         top_p=0.8,
#         function_call_behavior=FunctionCallBehavior.EnableFunctions(
#             auto_invoke=True, filters={"excluded_plugins": ["ChatBot"]}
#         ),
#     )

#     prompt_template_config = PromptTemplateConfig(
#         template="{{$input}}", description="Do math.", execution_settings=execution_settings
#     )

#     # Create the prompt function
#     kernel.add_function(
#         function_name="math_fun", plugin_name="math_int_test", prompt_template_config=prompt_template_config
#     )

#     summary = await retry(
#         lambda: kernel.invoke(function_name="math_fun", plugin_name="math_int_test", input="what is 1+1?")
#     )
#     output = str(summary).strip()
#     print(f"Math output: '{output}'")
#     assert "2" in output
#     assert len(output) > 0


# @pytest.mark.asyncio
# async def test_azure_oai_chat_service_with_tool_call_streaming(kernel: Kernel):
#     azure_openai_settings = AzureOpenAISettings.create()
#     endpoint = azure_openai_settings.endpoint
#     deployment_name = azure_openai_settings.chat_deployment_name
#     api_key = azure_openai_settings.api_key.get_secret_value()
#     api_version = azure_openai_settings.api_version

#     client = AsyncAzureOpenAI(
#         azure_endpoint=endpoint,
#         azure_deployment=deployment_name,
#         api_key=api_key,
#         api_version=api_version,
#         default_headers={"Test-User-X-ID": "test"},
#     )

#     # Configure LLM service
#     kernel.add_service(
#         sk_oai.AzureChatCompletion(
#             service_id="chat_completion",
#             async_client=client,
#         ),
#     )

#     kernel.add_plugin(MathPlugin(), plugin_name="Math")

#     # Create the prompt function
#     kernel.add_function(prompt="Keep the answer short. {{$input}}", function_name="chat", plugin_name="chat")
#     execution_settings = sk_oai.AzureChatPromptExecutionSettings(
#         service_id="chat_completion",
#         max_tokens=2000,
#         temperature=0.7,
#         top_p=0.8,
#         function_call_behavior=FunctionCallBehavior.EnableFunctions(
#             auto_invoke=True, filters={"excluded_plugins": ["ChatBot"]}
#         ),
#     )
#     arguments = KernelArguments(input="what is 101+102?", settings=execution_settings)

#     result: StreamingChatMessageContent | None = None
#     async for message in kernel.invoke_stream(function_name="chat", plugin_name="chat", arguments=arguments):
#         result = message[0] if not result else result + message[0]
#     output = str(result)

#     print(f"Math output: '{output}'")
#     assert "2" in output
#     assert 0 < len(output) < 500
