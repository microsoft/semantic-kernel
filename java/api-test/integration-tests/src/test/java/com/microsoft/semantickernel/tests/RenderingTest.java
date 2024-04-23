// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.aiservices.openai.textcompletion.OpenAITextGenerationService;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import java.util.List;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;

@WireMockTest
public class RenderingTest {

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
    public void textSemanticKernelTemplate() {
        buildTextKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        Value: {{$value}}
                        """)
                    .withTemplateFormat(PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT)
                    .build())
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("value", "{{$ignore}}")
                .withVariable("ignore", "dont show")
                .build())
            .block();

        Assertions.assertFalse(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("dont show"));
        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("{{$ignore}}"));
    }

    @Test
    public void textHandleBarsTemplate() {
        buildTextKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        Value: {{value}}
                        """)
                    .withTemplateFormat("handlebars")
                    .build())
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("value", "{{ignore}}")
                .withVariable("ignore", "dont show")
                .build())
            .block();

        Assertions.assertFalse(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("dont show"));
        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("{{ignore}}"));
    }

    @Test
    public void chatSemanticKernelTemplate() {
        buildChatKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        Value: {{$value}}
                        """)
                    .withTemplateFormat(PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT)
                    .build())
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("value", "{{$ignore}}")
                .withVariable("ignore", "dont show")
                .build())
            .block();

        Assertions.assertFalse(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("dont show"));
        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("{{$ignore}}"));
    }

    @Test
    public void chatHandleBarsTemplate() {
        buildChatKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        Value: {{value}}
                        """)
                    .withTemplateFormat("handlebars")
                    .build())
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("value", "{{ignore}}")
                .withVariable("ignore", "dont show")
                .build())
            .block();

        Assertions.assertFalse(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("dont show"));
        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("{{ignore}}"));
    }

    @Test
    public void chatSemanticKernelTemplate2() {
        buildChatKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        <message role="user">Value: {{$value}}</message>
                        """)
                    .withTemplateFormat(PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT)
                    .build())
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("value", "{{$ignore}}")
                .withVariable("ignore", "dont show")
                .build())
            .block();

        Assertions.assertFalse(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("dont show"));
        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().contains("{{$ignore}}"));
    }

    @DefineKernelFunction(name = "WithEmptyListReturn")
    public List<Integer> WithEmptyListReturn() {
        return List.of();
    }

    @DefineKernelFunction(name = "WithListReturn")
    public List<Integer> WithListReturn() {
        return List.of(1, 2, 3);
    }

    @DefineKernelFunction(name = "WithListReturn2", returnType = "java.util.List")
    public List<Integer> WithListReturn2() {
        return List.of(1, 2, 3);
    }

    @DefineKernelFunction(name = "WithListReturn3", returnType = "java.util.List")
    public Mono<List<Integer>> WithListReturn3() {
        return Mono.just(List.of(1, 2, 3));
    }

    @DefineKernelFunction(name = "WithListReturn4", returnType = "java.util.List")
    public Mono<List<Integer>> WithListReturn4() {
        return Mono.just(List.of());
    }

    @Test
    public void canHandleIterableReturnFromFunction() {
        buildChatKernel()
            .invokeAsync(
                KernelFunction
                    .createFromPrompt("""
                        <message role="user">{{RenderingTest-WithEmptyListReturn}}</message>
                        <message role="user">{{RenderingTest-WithListReturn}}</message>
                        <message role="user">{{RenderingTest-WithListReturn2}}</message>
                        <message role="user">{{RenderingTest-WithListReturn3}}</message>
                        <message role="user">{{RenderingTest-WithListReturn4}}</message>
                        """)
                    .withTemplateFormat("handlebars")
                    .build())
            .block();

        Assertions.assertTrue(
            wm.getAllServeEvents().get(0).getRequest().getBodyAsString().equals(
                "{\"messages\":["
                    + "{\"role\":\"user\",\"content\":\"[]\"},"
                    + "{\"role\":\"user\",\"content\":\"[1, 2, 3]\"},"
                    + "{\"role\":\"user\",\"content\":\"[1, 2, 3]\"},"
                    + "{\"role\":\"user\",\"content\":\"[1, 2, 3]\"},"
                    + "{\"role\":\"user\",\"content\":\"[]\"}"
                    + "],\"model\":\"gpt-35-turbo-2\"}"));
    }

    private Kernel buildTextKernel() {
        wm.addStubMapping(
            stubFor(
                ToolCallBehaviourTest.buildTextResponse(" ", """
                        "choices": [
                            {
                                "text": "Value: bar"
                            }
                        ]
                    """)));
        wm.start();

        final OpenAIAsyncClient client = new OpenAIClientBuilder()
            .endpoint("http://localhost:" + wm.port() + "/")
            .buildAsyncClient();

        TextGenerationService textGenerationService = OpenAITextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId("gpt-35-turbo-2")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(TextGenerationService.class, textGenerationService)
            .build();
        return kernel;
    }

    private Kernel buildChatKernel() {
        wm.addStubMapping(
            stubFor(
                ToolCallBehaviourTest.buildResponse(" ", """
                       "choices" : [
                          {
                             "finish_reason" : "stop",
                             "index" : 0,
                             "message" : {
                                "content" : "done",
                                "role" : "assistant"
                             }
                          }
                       ]
                    """)));
        wm.start();

        final OpenAIAsyncClient client = new OpenAIClientBuilder()
            .endpoint("http://localhost:" + wm.port() + "/")
            .buildAsyncClient();

        ChatCompletionService textGenerationService = OpenAIChatCompletion.builder()
            .withOpenAIAsyncClient(client)
            .withModelId("gpt-35-turbo-2")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, textGenerationService)
            .withPlugin(KernelPluginFactory.createFromObject(this, "RenderingTest"))
            .build();
        return kernel;
    }
}
