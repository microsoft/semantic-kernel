// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.openai.AzureOpenAIClient;
import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.syntaxexamples.skills.SearchEngineSkill;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import reactor.core.publisher.Mono;

import java.util.ArrayList;

// ReSharper disable once InconsistentNaming
public class Example04CombineLLMPromptsAndNativeCode {

    @Test
    public void run() {
        com.microsoft.openai.OpenAIAsyncClient client =
                new AzureOpenAIClient(
                        DefaultKernelTest.mockCompletionOpenAIAsyncClient(new ArrayList<>()));

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

        Assertions.assertEquals(
                "Gran Torre Santiago is the tallest building in South America summary",
                result.block().getResult());

        /*
        var result2 = await kernel.RunAsync(
                ask,
                search["Search"],
                sumSkill["Summarize"]
        );

        var result3 = await kernel.RunAsync(
                ask,
                search["Search"],
                sumSkill["Notegen"]
        );

        Console.WriteLine(ask + "\n");
        Console.WriteLine("Bing Answer: " + result1 + "\n");
        Console.WriteLine("Summary: " + result2 + "\n");
        Console.WriteLine("Notes: " + result3 + "\n");

         */
    }
}
