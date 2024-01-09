// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;

public class Example02PipelineTest {
    @Test
    public void run() {
        OpenAIAsyncClient client = DefaultKernelTest.mockCompletionOpenAIAsyncClient();
        Kernel kernel = DefaultKernelTest.buildKernel("model", client);

        // Load native skill
        ReadOnlyFunctionCollection text = kernel.importSkill(new TextSkill(), null);

        Mono<SKContext> result =
                kernel.runAsync(
                        "    i n f i n i t e     s p a c e     ",
                        text.getFunction("LStrip"),
                        text.getFunction("RStrip"),
                        text.getFunction("Uppercase"));

        Assertions.assertEquals("I N F I N I T E     S P A C E", result.block().getResult());
    }
}
