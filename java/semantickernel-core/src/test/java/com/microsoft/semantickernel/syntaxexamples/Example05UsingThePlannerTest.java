// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClientMatch;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatcher;

import reactor.util.function.Tuples;

public class Example05UsingThePlannerTest {

    public static SequentialPlanner getPlanner(Kernel kernel) {
        kernel.importSkillFromDirectory("SummarizeSkill", "../../samples/skills", "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", "../../samples/skills", "WriterSkill");

        return new SequentialPlanner(kernel, null, null);
    }

    @Test
    public void run() {
        ArgumentMatcher<String> matcher =
                prompt -> {
                    return prompt.contains(
                            "Create an XML plan step by step, to satisfy the goal given");
                };

        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClientMatch(Tuples.of(matcher, "A-PLAN"));

        KernelConfig config =
                SKBuilders.kernelConfig()
                        .addTextCompletionService(
                                "davinci",
                                kernel ->
                                        SKBuilders.textCompletionService()
                                                .build(client, "text-davinci-003"))
                        .build();

        Kernel kernel = SKBuilders.kernel().withKernelConfig(config).build();

        SequentialPlanner planner = getPlanner(kernel);
        System.out.println(
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian.")
                        .block()
                        .toEmbeddingString());
    }
}
