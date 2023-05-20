// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples; // Copyright (c) Microsoft. All rights
// reserved.

import com.azure.ai.openai.models.Choice;
import com.azure.ai.openai.models.Completions;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.syntaxexamples.skills.SearchEngineSkill;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import reactor.core.publisher.Mono;

import java.util.Arrays;

public class Example04CombineLLMPromptsAndNativeCodeTest {

    @Test
    public void run() {
        com.microsoft.openai.OpenAIAsyncClient client =
                Mockito.mock(com.microsoft.openai.OpenAIAsyncClient.class);

        Completions completion = Mockito.mock(Completions.class);
        Choice choice = Mockito.mock(Choice.class);
        Mockito.when(choice.getText()).thenReturn("A-SUMMARY");
        Mockito.when(completion.getChoices()).thenReturn(Arrays.asList(choice));
        Mockito.when(
                        client.getCompletions(
                                Mockito.any(),
                                Mockito.argThat(
                                        r -> {
                                            return r.getPrompt()
                                                    .get(0)
                                                    .contains(
                                                            "Gran Torre Santiago is the tallest"
                                                                    + " building in South America");
                                        })))
                .thenReturn(Mono.just(completion));

        KernelConfig kernelConfig =
                SKBuilders.kernelConfig()
                        .addTextCompletionService(
                                "text-davinci-002",
                                kernel -> new OpenAITextCompletion(client, "text-davinci-002"))
                        .addTextCompletionService(
                                "text-davinci-003",
                                kernel -> new OpenAITextCompletion(client, "text-davinci-003"))
                        .setDefaultTextCompletionService("text-davinci-003")
                        .build();

        Kernel kernel = SKBuilders.kernel().setKernelConfig(kernelConfig).build();
        kernel.importSkill(new SearchEngineSkill(), null);
        kernel.importSkill(
                "SummarizeSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../samples/skills", "SummarizeSkill"));

        // Run
        String ask = "What's the tallest building in South America?";

        Mono<SKContext<?>> result =
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
