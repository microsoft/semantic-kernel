// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.functions;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatMessageContent;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIFunctionToolCall;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.implementation.CollectionUtil;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.InvocationReturnMode;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.nio.charset.StandardCharsets;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

public class Example59_OpenAIFunctionCalling {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-3.5-turbo-1106");

    // Define functions that can be called by the model
    public static class HelperFunctions {

        @DefineKernelFunction(name = "currentUtcTime", description = "Retrieves the current time in UTC.")
        public String currentUtcTime() {
            return ZonedDateTime.now().format(DateTimeFormatter.RFC_1123_DATE_TIME);
        }

        @DefineKernelFunction(name = "getWeatherForCity", description = "Gets the current weather for the specified city")
        public String getWeatherForCity(
            @KernelFunctionParameter(name = "cityName", description = "Name of the city") String cityName) {
            switch (cityName) {
                case "Thrapston":
                    return "80 and sunny";
                case "Boston":
                    return "61 and rainy";
                case "London":
                    return "55 and cloudy";
                case "Miami":
                    return "80 and sunny";
                case "Paris":
                    return "60 and rainy";
                case "Tokyo":
                    return "50 and sunny";
                case "Sydney":
                    return "75 and sunny";
                case "Tel Aviv":
                    return "80 and sunny";
                default:
                    return "31 and snowing";
            }
        }
    }

    public static void main(String[] args) throws NoSuchMethodException {
        System.out.println("======== Open AI - Function calling ========");

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        ChatCompletionService chat = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        var plugin = KernelPluginFactory.createFromObject(new HelperFunctions(), "HelperFunctions");

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chat)
            .withPlugin(plugin)
            .build();

        System.out.println("======== Example 1: Use automated function calling ========");

        var function = KernelFunctionFromPrompt.builder()
            .withTemplate(
                "Given the current time of day and weather, what is the likely color of the sky in Boston?")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withTemperature(0.4)
                    .withTopP(1)
                    .withMaxTokens(100)
                    .build())
            .build();

        var result = kernel
            .invokeAsync(function)
            .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(true))
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
            .block();
        System.out.println(result.getResult());

        System.out.println("======== Example 2: Use manual function calling ========");

        var chatHistory = new ChatHistory();
        chatHistory.addUserMessage(
            "Given the current time of day and weather, what is the likely color of the sky in Boston?");

        while (true) {
            var messages = chat.getChatMessageContentsAsync(
                chatHistory,
                kernel,
                InvocationContext.builder()
                    .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(false))
                    .withReturnMode(InvocationReturnMode.FULL_HISTORY)
                    .build())
                .block();

            chatHistory = new ChatHistory(messages);

            ChatMessageContent<?> lastMessage = CollectionUtil.getLastOrNull(messages);

            List<OpenAIFunctionToolCall> toolCalls = null;

            if (lastMessage instanceof OpenAIChatMessageContent) {
                toolCalls = ((OpenAIChatMessageContent<?>) lastMessage).getToolCall();
            }

            if (toolCalls == null || toolCalls.isEmpty()) {
                break;
            }

            for (OpenAIFunctionToolCall toolCall : toolCalls) {
                String content;
                try {
                    // getFunction will throw an exception if the function is not found
                    var fn = kernel.getFunction(toolCall.getPluginName(),
                        toolCall.getFunctionName());
                    FunctionResult<?> fnResult = fn
                        .invokeAsync(kernel, toolCall.getArguments(), null, null).block();
                    content = (String) fnResult.getResult();
                } catch (IllegalArgumentException e) {
                    content = "Unable to find function. Please try again!";
                }

                chatHistory.addMessage(
                    AuthorRole.TOOL,
                    content,
                    StandardCharsets.UTF_8,
                    FunctionResultMetadata.build(toolCall.getId()));
            }
        }

        chatHistory.getMessages().stream()
            .filter(it -> it.getContent() != null)
            .forEach(it -> System.out.println(it.getContent()));

    }

}
