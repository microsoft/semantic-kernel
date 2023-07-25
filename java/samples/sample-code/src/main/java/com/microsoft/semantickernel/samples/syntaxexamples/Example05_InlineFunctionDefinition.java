// Copyright (c) Microsoft. All rights reserved.

package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

public class Example05_InlineFunctionDefinition {
    public static void main(String[] args) throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();

        TextCompletion textCompletion = SKBuilders.textCompletionService().build(client, "text-davinci-003");

        KernelConfig kernelConfig = new KernelConfig.Builder()
                .addTextCompletionService("text-davinci-003", kernel -> textCompletion)
                .build();

        Kernel kernel = SKBuilders.kernel().withKernelConfig(kernelConfig).build();

        System.out.println("======== Inline Function Definition ========");

        // Function defined using few-shot design pattern
        String functionDefinition = """
                    Generate a creative reason or excuse for the given event.
                    Be creative and be funny. Let your imagination run wild.
                    
                    Event: I am running late.
                    Excuse: I was being held ransom by giraffe gangsters.
                    
                    Event: I haven't been to the gym for a year
                    Excuse: I've been too busy training my pet dragon.
                    
                    Event: {{$input}}
                """.stripIndent();

        // Create function via builder
        var excuseFunction = SKBuilders
                .completionFunctions(kernel)
                .createFunction(
                        functionDefinition,
                        new PromptTemplateConfig.CompletionConfigBuilder()
                                .maxTokens(100)
                                .temperature(0.4)
                                .topP(1)
                                .build());


        var result = excuseFunction.invokeAsync("I missed the F1 final race").block();
        System.out.println(result.getResult());

        result = excuseFunction.invokeAsync("sorry I forgot your birthday").block();
        System.out.println(result.getResult());

        // Create function via kernel
        var fixedFunction = kernel.
                getSemanticFunctionBuilder()
                .createFunction("Translate this date " +
                                DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(LocalDateTime.now()) + " to French format",
                        new PromptTemplateConfig.CompletionConfigBuilder()
                                .maxTokens(100)
                                .temperature(0.4)
                                .topP(1)
                                .build());

        System.out.println(fixedFunction.invokeAsync().block().getResult());
    }
}
