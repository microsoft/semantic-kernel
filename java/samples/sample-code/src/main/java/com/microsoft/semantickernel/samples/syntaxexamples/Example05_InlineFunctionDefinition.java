// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;


import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public class Example05_InlineFunctionDefinition {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "text-davinci-003");

    public static void main(String[] args) throws ConfigurationException {

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        TextGenerationService textGenerationService = TextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(TextGenerationService.class, textGenerationService)
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
                
                Event: {{$input}}
            """.stripIndent();

        var excuseFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(promptTemplate)
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
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
        System.out.println(result.getResult());

        result = kernel.invokeAsync(excuseFunction,
                KernelArguments.builder()
                    .withInput("sorry I forgot your birthday")
                    .build(),
                String.class)
            .block();
        System.out.println(result.getResult());

        var fixedFunction = KernelFunctionFactory.createFromPrompt(
            "Translate this date " + DateTimeFormatter
                .ISO_LOCAL_DATE
                .withZone(ZoneOffset.UTC)
                .format(Instant.ofEpochSecond(1))
                + " to French format",
            PromptExecutionSettings.builder()
                .withMaxTokens(100)
                .build(),
            null,
            null,
            null,
            null);

        FunctionResult<String> fixedFunctionResult = kernel
            .invokeAsync(fixedFunction, null, String.class)
            .block();
        System.out.println(fixedFunctionResult.getResult());

    }
}
