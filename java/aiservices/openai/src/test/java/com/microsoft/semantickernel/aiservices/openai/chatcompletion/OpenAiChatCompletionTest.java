// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsFunctionToolCall;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatRequestAssistantMessage;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.rest.Response;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import java.nio.charset.Charset;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Mono;

public class OpenAiChatCompletionTest {

    @Test
    public void serializesToolCallsCorrectly() {
        OpenAIAsyncClient client = Mockito.mock(OpenAIAsyncClient.class);
        OpenAIChatCompletion chatCompletion = mockClient(client);

        ChatHistory chatHistory = new ChatHistory();

        chatHistory.addUserMessage(
            "What is the name of the pet with id ca2fc6bc-1307-4da6-a009-d7bf88dec37b?");

        chatHistory.addMessage(new OpenAIChatMessageContent(
            AuthorRole.ASSISTANT,
            "",
            "test",
            null,
            Charset.defaultCharset(),
            null,
            Arrays.asList(
                new OpenAIFunctionToolCall(
                    "a-tool-id",
                    "pluginName",
                    "funcName",
                    KernelFunctionArguments.builder()
                        .withVariable("id", "ca2fc6bc-1307-4da6-a009-d7bf88dec37b")
                        .build()))));
        chatHistory.addMessage(new OpenAIChatMessageContent(
            AuthorRole.TOOL,
            "Snuggles",
            "test",
            null,
            Charset.defaultCharset(),
            FunctionResultMetadata.build("a-tool-id"),
            null));

        chatCompletion
            .getChatMessageContentsAsync(chatHistory, null, null).block();

        Mockito.verify(client, Mockito.times(1))
            .getChatCompletionsWithResponse(
                Mockito.any(),
                Mockito.<ChatCompletionsOptions>argThat(options -> {
                    ChatRequestAssistantMessage message = ((ChatRequestAssistantMessage) options
                        .getMessages()
                        .get(1));
                    ChatCompletionsFunctionToolCall toolcall = ((ChatCompletionsFunctionToolCall) message
                        .getToolCalls()
                        .get(0));
                    return toolcall
                        .getFunction()
                        .getArguments()
                        .equals("{\"id\": \"ca2fc6bc-1307-4da6-a009-d7bf88dec37b\"}");
                }),
                Mockito.any());
    }

    private static OpenAIChatCompletion mockClient(OpenAIAsyncClient client) {
        Mockito.when(client.getChatCompletionsWithResponse(Mockito.any(),
            Mockito.<ChatCompletionsOptions>any(), Mockito.any()))
            .thenReturn(Mono.just(
                new Response<ChatCompletions>() {
                    @Override
                    public int getStatusCode() {
                        return 200;
                    }

                    @Override
                    public HttpHeaders getHeaders() {
                        return new HttpHeaders();
                    }

                    @Override
                    public HttpRequest getRequest() {
                        return null;
                    }

                    @Override
                    public ChatCompletions getValue() {
                        try {
                            String message = EmbeddedResourceLoader.readFile("chatCompletion.txt",
                                OpenAiChatCompletionTest.class);

                            return new ObjectMapper()
                                .readValue(String.format(message, "Snuggles"),
                                    ChatCompletions.class);

                        } catch (Exception e) {
                            throw new RuntimeException(e);
                        }
                    }
                }));
        return new OpenAIChatCompletion(
            client,
            "test",
            "test",
            "test");
    }

}
