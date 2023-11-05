// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

/**
 * Demonstrates using skill in combination with LLM prompts.
 * <p>
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class Example04_CombineLLMPromptsAndNativeCode {

  public static class SearchEngineSkill {

    @DefineSKFunction(description = "Search for answer", name = "search")
    public Mono<String> search(
        @SKFunctionInputAttribute(description = "Text to search")
        String input) {
      return Mono.just("Gran Torre Santiago is the tallest building in South America");
    }
  }

  public static void main(String[] args) throws ConfigurationException {
    OpenAIAsyncClient client = SamplesConfig.getClient();

        TextCompletion textCompletion = SKBuilders.textCompletion()
                .withModelId("text-davinci-003")
        .withOpenAIClient(client)
        .build();

        Kernel kernel = SKBuilders.kernel().withDefaultAIService(textCompletion).build();
    kernel.importSkill(new SearchEngineSkill(), null);
    kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(),
        "SummarizeSkill");


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
