// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;


import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.azureopenai.AzureOpenAITextGenerationService;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public class Example05_InlineFunctionDefinition {

    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
        System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    public static void main(String[] args) throws ConfigurationException {

        TextGenerationService textGenerationService;

        if (USE_AZURE_CLIENT) {
            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

            textGenerationService = AzureOpenAITextGenerationService.builder()
                .withOpenAIAsyncClient(client)
                .withModelId("text-davinci-003")
                .build();
        } else {
            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();

            // TODO: Add support for OpenAI API
            textGenerationService = null;
        }

        Kernel kernel = new DefaultKernel.Builder()
            .withDefaultAIService(TextGenerationService.class, textGenerationService)
            .build();

        System.out.println("======== Inline Function Definition ========");

        // Function defined using few-shot design pattern
        String promptTemplate = """
                Generate a creative reason or excuse for the given event.
                Be creative and be funny. Let your imagination run wild.
                
                Event: I am running late.
                Excuse: I was being held ransom by giraffe gangsters.
                
                Event: I haven't been to the gym for a year
                Excuse: I've been too busy training my pet dragon.
                
                Event: {{input}}
            """.stripIndent();

        var excuseFunction = new KernelFunctionFromPrompt.Builder()
            .withTemplate(promptTemplate)
            .withDefaultExecutionSettings(
                new PromptExecutionSettings.Builder()
                    .withTemperature(0.4)
                    .withTopP(1)
                    .withMaxTokens(100)
                    .build()
            )
            .build();

        var result = kernel.invokeAsync(excuseFunction,
                KernelArguments.builder()
                    .withInput("I missed the F1 final race")
                    .build(),
                String.class)
            .block();
        System.out.println(result.getValue());

        result = kernel.invokeAsync(excuseFunction,
                KernelArguments.builder()
                    .withInput("sorry I forgot your birthday")
                    .build(),
                String.class)
            .block();
        System.out.println(result.getValue());

        var fixedFunction = KernelFunctionFactory.createFromPrompt(
            "Translate this date " + DateTimeFormatter
                .ISO_LOCAL_DATE
                .withZone(ZoneOffset.UTC)
                .format(Instant.now())
                + " to French format",
            new PromptExecutionSettings.Builder()
                .withMaxTokens(100)
                .build(),
            null,
            null,
            null,
            null);

        ContextVariable<String> fixedFunctionResult = kernel
            .invokeAsync(fixedFunction, null, String.class)
            .block();
        System.out.println(fixedFunctionResult.getValue());

    }
}
