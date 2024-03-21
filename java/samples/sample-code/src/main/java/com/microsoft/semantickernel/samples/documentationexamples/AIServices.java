// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;

public class AIServices {

    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String CHAT_MODEL_ID = System.getenv()
        .getOrDefault("CHAT_MODEL_ID", "gpt-3.5-turbo");
    private static final String TEXT_MODEL_ID = System.getenv()
        .getOrDefault("TEXT_MODEL_ID", "text-davinci-002");

    public static void main(String[] args) {
        System.out.println("======== AI Services ========");

        OpenAIAsyncClient client = null;

        if (AZURE_CLIENT_KEY != null && CLIENT_ENDPOINT != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
        } else if (CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        } else {
            System.out.println("No client key found");
            return;
        }

        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(CHAT_MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        TextGenerationService textGenerationService = TextGenerationService.builder()
            .withModelId(TEXT_MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withAIService(TextGenerationService.class, textGenerationService)
            .build();

    }
}
