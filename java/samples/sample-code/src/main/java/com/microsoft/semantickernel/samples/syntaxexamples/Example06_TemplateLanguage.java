// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.samples.Config;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.TimeSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

import java.io.IOException;

public class Example06_TemplateLanguage {
    /// <summary>
    /// Show how to invoke a Native Function written in C#
    /// from a Semantic Function written in natural language
    /// </summary>

    public static void main(String[] args) throws IOException {
        System.out.println("======== TemplateLanguage ========");

        OpenAIAsyncClient client = Config.getClient();
        KernelConfig kernelConfig = SKBuilders
                .kernelConfig()
                .addTextCompletionService("text-davinci-003", kernel1 -> SKBuilders.textCompletionService()
                        .build(client, "text-davinci-003"))
                .build();

        Kernel kernel = SKBuilders.kernel()
                .withKernelConfig(kernelConfig)
                .build();

        // Load native skill into the kernel skill collection, sharing its functions
        // with prompt templates
        // Functions loaded here are available as "time.*"
        kernel.importSkill(new TimeSkill(), "time");

        // Semantic Function invoking time.Date and time.Time native functions
        String functionDefinition = """
                Today is: {{time.Date}}
                Current time is: {{time.Time}}

                Answer to the following questions using JSON syntax, including the data used.
                Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
                Is it weekend time (weekend/not weekend)?
                """;

        // This allows to see the prompt before it's sent to OpenAI
        System.out.println("--- Rendered Prompt");

        var promptRenderer = SKBuilders.promptTemplate()
                .withPromptTemplateConfig(new PromptTemplateConfig())
                .withPromptTemplate(functionDefinition)
                .build(kernel.getPromptTemplateEngine());

        SKContext skContext = SKBuilders
                .context()
                .build(kernel.getSkills());

        var renderedPrompt = promptRenderer.renderAsync(skContext);
        System.out.println(renderedPrompt.block());

        // Run the prompt / semantic function
        var kindOfDay = kernel
                .getSemanticFunctionBuilder()
                .createFunction(
                        functionDefinition,
                        null,
                        null,
                        null,
                        new PromptTemplateConfig.CompletionConfig(
                                0, 0, 0, 0, 256));

        // Show the result
        System.out.println("--- Semantic Function result");
        var result = kindOfDay.invokeAsync("").block().getResult();
        System.out.println(result);
        /*
         * OUTPUT:
         *
         * --- Rendered Prompt
         *
         * Today is: Friday, April 28, 2023
         * Current time is: 11:04:30 PM
         *
         * Answer to the following questions using JSON syntax, including the data used.
         * Is it morning, afternoon, evening, or night
         * (morning/afternoon/evening/night)?
         * Is it weekend time (weekend/not weekend)?
         *
         * --- Semantic Function result
         *
         * {
         * "date": "Friday, April 28, 2023",
         * "time": "11:04:30 PM",
         * "period": "night",
         * "weekend": "weekend"
         * }
         */
    }
}
