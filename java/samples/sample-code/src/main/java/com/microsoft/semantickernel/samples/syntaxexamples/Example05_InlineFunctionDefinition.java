// Copyright (c) Microsoft. All rights reserved.

package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

/**
 * Demonstrates using prompt templates to define functions.
 * <p>
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class Example05_InlineFunctionDefinition {
  public static void main(String[] args) throws ConfigurationException {
    OpenAIAsyncClient client = SamplesConfig.getClient();

    TextCompletion textCompletion = SKBuilders.textCompletion()
        .withModelId("text-davinci-003")
        .withOpenAIClient(client)
        .build();

    Kernel kernel = SKBuilders.kernel().withDefaultAIService(textCompletion).build();

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
        .completionFunctions()
        .withKernel(kernel)
        .withPromptTemplate(functionDefinition)
        .withCompletionConfig(
            new PromptTemplateConfig.CompletionConfigBuilder()
                .maxTokens(100)
                .temperature(0.4)
                .topP(1)
                .build())
        .build();


    var result = excuseFunction.invokeAsync("I missed the F1 final race").block();
    System.out.println(result.getResult());

    result = excuseFunction.invokeAsync("sorry I forgot your birthday").block();
    System.out.println(result.getResult());

    // Create function via kernel
    var fixedFunction = kernel.
        getSemanticFunctionBuilder()
        .withPromptTemplate("Translate this date " +
            DateTimeFormatter.ofLocalizedDate(FormatStyle.FULL).format(LocalDateTime.now()) + " to French format")
        .withCompletionConfig(
            new PromptTemplateConfig.CompletionConfigBuilder()
                .maxTokens(100)
                .temperature(0.4)
                .topP(1)
                .build())
        .build();

    System.out.println(fixedFunction.invokeAsync().block().getResult());
  }
}
