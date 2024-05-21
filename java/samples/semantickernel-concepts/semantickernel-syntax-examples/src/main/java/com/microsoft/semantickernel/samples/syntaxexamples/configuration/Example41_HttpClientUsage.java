// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.configuration;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;

public class Example41_HttpClientUsage {

    public static void main(String[] args) {
        useDefaultHttpClient();
        useCustomHttpClient();
    }

    /// <summary>
    /// Demonstrates the usage of the default HttpClient provided by the SK SDK.
    /// </summary>
    private static void useDefaultHttpClient() {
        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new AzureKeyCredential("a-key"))
            .endpoint("an-endpoint")
            .buildAsyncClient();

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class,
                OpenAIChatCompletion.builder()
                    .withOpenAIAsyncClient(client)
                    .withModelId("gpt-35-turbo-2")
                    .build())
            .build();
    }

    /// <summary>
    /// Demonstrates the usage of a custom HttpClient.
    /// </summary>
    private static void useCustomHttpClient() {
        HttpClient customHttpClient = HttpClient.createDefault();

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .httpClient(customHttpClient)
            .endpoint("https://localhost:5000")
            .credential(new AzureKeyCredential("BAD KEY"))
            .buildAsyncClient();

        TextGenerationService textGenerationService = TextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId("text-davinci-003")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(TextGenerationService.class, textGenerationService)
            .build();
    }
}
