// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.syntaxexamples.skills.SearchEngineSkill;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuples;

public class Example04CombineLLMPromptsAndNativeCodeTest {

    @Test
    public void run() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of(
                                "Gran Torre Santiago is the tallest building in South America",
                                "A-SUMMARY"));

        Kernel kernel =
                SKBuilders.kernel()
                        .withAIService(
                                "text-davinci-002",
                                new OpenAITextCompletion(client, "text-davinci-002"),
                                false,
                                TextCompletion.class)
                        .withAIService(
                                "text-davinci-003",
                                new OpenAITextCompletion(client, "text-davinci-003"),
                                true,
                                TextCompletion.class)
                        .build();

        kernel.importSkill(new SearchEngineSkill(), null);
        kernel.importSkillFromDirectory("SummarizeSkill", "../../samples/skills", "SummarizeSkill");

        // Run
        String ask = "What's the tallest building in South America?";

        Mono<SKContext> result =
                kernel.runAsync(ask, kernel.getSkills().getFunction("Search", null));

        Assertions.assertEquals(
                "Gran Torre Santiago is the tallest building in South America",
                result.block().getResult());

        result =
                kernel.runAsync(
                        ask,
                        kernel.getSkills().getFunction("Search", null),
                        kernel.getSkill("SummarizeSkill").getFunction("Summarize", null));

        Assertions.assertEquals("A-SUMMARY", result.block().getResult());
    }
}
