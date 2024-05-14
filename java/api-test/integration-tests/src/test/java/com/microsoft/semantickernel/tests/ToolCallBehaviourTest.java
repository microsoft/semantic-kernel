// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.client.MappingBuilder;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import com.github.tomakehurst.wiremock.matching.ContainsPattern;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatMessageContent;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIFunctionToolCall;
import com.microsoft.semantickernel.implementation.CollectionUtil;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

@WireMockTest
public class ToolCallBehaviourTest {

    private WireMockServer wm;

    @BeforeEach
    public void before() {
        wm = new WireMockServer();
    }

    @AfterEach
    public void after() {
        wm.stop();
    }

    @Test
    public void nonAutoInvokedIsNotCalled() throws NoSuchMethodException {
        ChatCompletionService chatCompletionService = getChatCompletionService();

        TestPlugin testPlugin = Mockito.spy(new TestPlugin());
        KernelFunction<String> method = KernelFunctionFromMethod.<String>builder()
            .withFunctionName("doIt")
            .withMethod(TestPlugin.class.getMethod("doIt"))
            .withTarget(testPlugin)
            .withPluginName("apluginname")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(
                new KernelPlugin(
                    "apluginname",
                    "A plugin description",
                    Map.of("doIt", method)))
            .build();

        ChatHistory messages = new ChatHistory();
        messages.addMessage(
            new ChatMessageContent<>(
                AuthorRole.USER,
                "Call A function"));

        List<ChatMessageContent<?>> result = chatCompletionService
            .getChatMessageContentsAsync(
                messages,
                kernel,
                InvocationContext.builder()
                    .withToolCallBehavior(
                        ToolCallBehavior.allowOnlyKernelFunctions(false, method))
                    .build())
            .block();

        List<OpenAIFunctionToolCall> toolCalls = ((OpenAIChatMessageContent<?>) CollectionUtil.getLastOrNull(result))
            .getToolCall();

        Assertions.assertNotNull(toolCalls);
        Assertions.assertEquals(1, toolCalls.size());
        Assertions.assertEquals("apluginname", CollectionUtil.getLastOrNull(toolCalls).getPluginName());
        Assertions.assertEquals("doIt", CollectionUtil.getLastOrNull(toolCalls).getFunctionName());
        Assertions.assertEquals("call_abc123", CollectionUtil.getLastOrNull(toolCalls).getId());

        Mockito.verify(testPlugin, Mockito.times(0)).doIt();
    }

    @Test
    public void toolIsInvoked() throws NoSuchMethodException {
        ChatCompletionService chatCompletionService = getChatCompletionService();

        TestPlugin testPlugin = Mockito.spy(new TestPlugin());
        KernelFunction<String> method = KernelFunctionFromMethod.<String>builder()
            .withFunctionName("doIt")
            .withMethod(TestPlugin.class.getMethod("doIt"))
            .withTarget(testPlugin)
            .withPluginName("apluginname")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(
                new KernelPlugin(
                    "apluginname",
                    "A plugin description",
                    Map.of("doIt", method)))
            .build();

        ChatHistory messages = new ChatHistory();
        messages.addMessage(
            new ChatMessageContent<>(
                AuthorRole.USER,
                "Call A function"));

        List<ChatMessageContent<?>> result = chatCompletionService
            .getChatMessageContentsAsync(
                messages,
                kernel,
                InvocationContext.builder()
                    .withToolCallBehavior(
                        ToolCallBehavior.allowAllKernelFunctions(true))
                    .build())
            .block();

        Assertions.assertTrue(CollectionUtil.getLastOrNull(result).getContent().contains("tool call done"));
        Mockito.verify(testPlugin, Mockito.times(1)).doIt();

        result = chatCompletionService
            .getChatMessageContentsAsync(
                messages,
                kernel,
                InvocationContext.builder()
                    .withToolCallBehavior(
                        ToolCallBehavior.allowOnlyKernelFunctions(true, Arrays.asList(method)))
                    .build())
            .block();

        Assertions.assertTrue(
            CollectionUtil.getLastOrNull(result).getContent().contains("tool call done"));
        Mockito.verify(testPlugin, Mockito.times(2)).doIt();

        result = chatCompletionService
            .getChatMessageContentsAsync(
                messages,
                kernel,
                InvocationContext.builder()
                    .withToolCallBehavior(
                        ToolCallBehavior.allowOnlyKernelFunctions(true, method))
                    .build())
            .block();

        Assertions.assertTrue(CollectionUtil.getLastOrNull(result).getContent().contains("tool call done"));
        Mockito.verify(testPlugin, Mockito.times(3)).doIt();
    }

    private ChatCompletionService getChatCompletionService() {
        wm
            .addStubMapping(
                stubFor(
                    buildResponse("Call A function", """
                        "choices": [
                          {
                            "index": 0,
                            "message": {
                              "role": "assistant",
                              "content": null,
                              "tool_calls": [
                                {
                                  "id": "call_abc123",
                                  "type": "function",
                                  "function": {
                                    "name": "apluginname-doIt",
                                    "arguments": "{}"
                                  }
                                }
                              ]
                            },
                            "logprobs": null,
                            "finish_reason": "tool_calls"
                          }
                        ]
                        """)));

        wm.addStubMapping(
            stubFor(
                buildResponse("Tool call performed", """
                       "choices" : [
                          {
                             "finish_reason" : "stop",
                             "index" : 0,
                             "message" : {
                                "content" : "tool call done",
                                "role" : "assistant"
                             }
                          }
                       ]
                    """)));

        wm.start();

        final OpenAIAsyncClient client = new OpenAIClientBuilder()
            .endpoint("http://localhost:" + wm.port() + "/")
            .buildAsyncClient();

        return ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId("gpt-35-turbo-2")
            .build();
    }

    public static MappingBuilder buildTextResponse(String bodyMatcher, String responseBody) {
        return post(urlEqualTo(
            "//openai/deployments/gpt-35-turbo-2/completions?api-version=2024-02-15-preview"))
            .withRequestBody(new ContainsPattern(bodyMatcher))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody(formTextResponse(responseBody)));
    }

    public static MappingBuilder buildResponse(String bodyMatcher, String responseBody) {
        return post(urlEqualTo(
            "//openai/deployments/gpt-35-turbo-2/chat/completions?api-version=2024-02-15-preview"))
            .withRequestBody(new ContainsPattern(bodyMatcher))
            .willReturn(
                aResponse()
                    .withStatus(200)
                    .withHeader("Content-Type", "application/json")
                    .withBody(formResponse(responseBody)));
    }

    public static class TestPlugin {

        public String doIt() {
            return "Tool call performed";
        }
    }

    private static String formTextResponse(String chatChoices) {
        return """
                    {
                        "id": "cmpl-3QJ9z1J9z1J9z1J9z1J9z1J9",
                        "usage": {
                            "total_tokens": 4,
                            "completion_tokens": 1,
                            "prompt_tokens": 1
                        },
                        %s
                    }
            """.formatted(chatChoices);
    }

    private static String formResponse(String chatChoices) {
        return """
            {
                %s,
               "created" : 1707253061,
               "id" : "chatcmpl-xxx",
               "model" : "gpt-35-turbo",
               "object" : "chat.completion",
               "prompt_filter_results" : [
                  {
                     "content_filter_results" : {
                        "hate" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "self_harm" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "sexual" : {
                           "filtered" : false,
                           "severity" : "safe"
                        },
                        "violence" : {
                           "filtered" : false,
                           "severity" : "safe"
                        }
                     },
                     "prompt_index" : 0
                  }
               ],
               "usage" : {
                  "completion_tokens" : 67,
                  "prompt_tokens" : 17,
                  "total_tokens" : 84
               }
            }
            """.formatted(chatChoices);
    }
}
