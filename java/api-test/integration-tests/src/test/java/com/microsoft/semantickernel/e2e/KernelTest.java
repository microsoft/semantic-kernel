// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import reactor.core.publisher.Mono;

import java.io.IOException;

public class KernelTest extends AbstractKernelTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(KernelTest.class);

    private static void executeCompletion(Kernel kernel) {
        CompletionSKFunction summarize =
                kernel.getSemanticFunctionBuilder()
                        .createFunction(
                                """
                                {{$input}}

                                One line TLDR with the fewest words.""",
                                null,
                                "",
                                null,
                                new PromptTemplateConfig.CompletionConfig(0, 0, 0, 0, 256));

        String text1 =
                """
                1st Law of Thermodynamics - Energy cannot be created or destroyed.
                2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
                3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy""";

        Mono<SKContext> mono = summarize.invokeAsync(text1);
        SKContext result = mono.block();

        if (result != null) LOGGER.info("Result: " + result.getResult());
    }

    public static Kernel buildKernel(OpenAIAsyncClient client, String model) {

        TextCompletion textCompletion = new OpenAITextCompletion(client, model);

        KernelConfig kernelConfig =
                SKBuilders.kernelConfig()
                        .addTextCompletionService(model, kernel -> textCompletion)
                        .build();

        return SKBuilders.kernel().withKernelConfig(kernelConfig).build();
    }

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void endToEndTextGenerationTestAzureOpenAI() throws IOException {
        Kernel kernel = buildKernel(getAzureOpenAIClient(), "text-davinci-003");
        executeCompletion(kernel);
    }

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void endToEndTextGenerationTestOpenAI() throws IOException {
        Kernel kernel = buildKernel(getOpenAIClient(), getOpenAIModel());
        executeCompletion(kernel);
    }
}
