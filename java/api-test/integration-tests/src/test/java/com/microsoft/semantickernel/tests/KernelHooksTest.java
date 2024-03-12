// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.tests;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.github.tomakehurst.wiremock.junit5.WireMockRuntimeInfo;
import com.github.tomakehurst.wiremock.junit5.WireMockTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Kernel.Builder;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

@WireMockTest
public class KernelHooksTest {

    private static Builder getKernelBuilder(WireMockRuntimeInfo wmRuntimeInfo) {
        final OpenAIAsyncClient client = new OpenAIClientBuilder()
            .endpoint("http://localhost:" + wmRuntimeInfo.getHttpPort())
            .buildAsyncClient();

        ChatCompletionService openAIChatCompletion = OpenAIChatCompletion.builder()
            .withModelId("text-davinci-003")
            .withOpenAIAsyncClient(client)
            .build();

        return Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion);
    }

    @Test
    public void getUsageAsync(WireMockRuntimeInfo wmRuntimeInfo) {
        WireMockUtil.mockChatCompletionResponse("Write a random paragraph about", "a-response");
        Kernel kernel = getKernelBuilder(wmRuntimeInfo).build();

        System.out.println("\n======== Get Usage Data ========\n");

        // Initialize prompt
        String functionPrompt = "Write a random paragraph about: {{$input}}.";

        KernelFunction<String> excuseFunction = KernelFunctionFromPrompt.<String>builder()
            .withTemplate(functionPrompt)
            .withName("Excuse")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(100)
                .withTemperature(0.4)
                .withTopP(1)
                .build())
            .withOutputVariable(new OutputVariable("java.lang.String", "result"))
            .build();

        AtomicBoolean preHookTriggered = new AtomicBoolean(false);

        FunctionInvokingHook preHook = event -> {
            preHookTriggered.set(true);
            return event;
        };

        AtomicBoolean removedPreExecutionHandlerTriggered = new AtomicBoolean(false);

        FunctionInvokingHook removedPreExecutionHandler = event -> {
            removedPreExecutionHandlerTriggered.set(true);
            return event;
        };

        AtomicBoolean postExecutionHandlerTriggered = new AtomicBoolean(false);

        FunctionInvokedHook postExecutionHandler = event -> {
            postExecutionHandlerTriggered.set(true);
            return event;
        };

        kernel.getGlobalKernelHooks().addHook(preHook);

        // Demonstrate pattern for removing a handler.
        kernel.getGlobalKernelHooks().addHook("pre-invoke-removed", removedPreExecutionHandler);
        kernel.getGlobalKernelHooks().removeHook("pre-invoke-removed");
        kernel.getGlobalKernelHooks().addHook(postExecutionHandler);

        kernel.invokeAsync(
            excuseFunction)
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .withVariable("input", "I missed the F1 final race")
                    .build())
            .block();

        Assertions.assertTrue(preHookTriggered.get());
        Assertions.assertFalse(removedPreExecutionHandlerTriggered.get());
        Assertions.assertTrue(postExecutionHandlerTriggered.get());
    }
}
