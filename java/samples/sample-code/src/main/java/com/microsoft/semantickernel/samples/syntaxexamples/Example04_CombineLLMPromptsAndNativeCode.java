// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Config;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

import java.io.IOException;

public class Example04_CombineLLMPromptsAndNativeCode {

    public static class SearchEngineSkill {
        @DefineSKFunction(description = "Append the day variable", name = "search")
        public Mono<String> search(
                @SKFunctionInputAttribute
                @SKFunctionParameters(description = "Text to search", name = "input")
                String input) {
            return Mono.just("Gran Torre Santiago is the tallest building in South America");
        }
    }

    public static void main(String[] args) throws IOException {
        OpenAIAsyncClient client = Config.getClient();

        TextCompletion textCompletion = SKBuilders.textCompletionService().build(client, "text-davinci-003");

        KernelConfig kernelConfig = new KernelConfig.Builder()
                .addTextCompletionService("text-davinci-003", kernel -> textCompletion)
                .build();

        Kernel kernel = SKBuilders.kernel().withKernelConfig(kernelConfig).build();
        kernel.importSkill(new SearchEngineSkill(), null);
        kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");

        // Run
        String ask = "What's the tallest building in South America?";

        Mono<SKContext> result =
                kernel.runAsync(ask, kernel.getSkills().getFunction("Search", null));

        result =
                kernel.runAsync(
                        ask,
                        kernel.getSkills().getFunction("Search", null),
                        kernel.getSkill("SummarizeSkill").getFunction("Summarize", null));

        System.out.println(result.block().getResult());
    }
}
