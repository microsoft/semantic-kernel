// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.syntaxexamples.skills.StaticTextSkill;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import reactor.core.publisher.Mono;

import java.util.ArrayList;

public class Example03VariablesTest {
    @Test
    public void run() {
        com.azure.ai.openai.OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClient(new ArrayList<>());
        Kernel kernel = DefaultKernelTest.buildKernel("model", client);

        // Load native skill
        ReadOnlyFunctionCollection functionCollection =
                kernel.importSkill(new StaticTextSkill(), "text");

        ContextVariables variables =
                SKBuilders.variables()
                        .build("Today is: ")
                        .writableClone()
                        .setVariable("day", "Monday");

        Mono<SKContext<?>> result =
                kernel.runAsync(
                        variables,
                        functionCollection.getFunction("AppendDay"),
                        functionCollection.getFunction("Uppercase"));

        Assertions.assertEquals("TODAY IS: MONDAY", result.block().getResult());
    }
}
