// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.configuration;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.identity.DeviceCodeCredential;
import com.azure.identity.DeviceCodeCredentialBuilder;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;

public class Example26_AADAuth {

    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) throws ConfigurationException {

        DeviceCodeCredential token = new DeviceCodeCredentialBuilder()
            .build();

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(token)
            .endpoint(CLIENT_ENDPOINT)
            .buildAsyncClient();

        ChatCompletionService chatService = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatService)
            .build();

        var chatHistory = new ChatHistory();

        // User message
        chatHistory.addUserMessage("Tell me a joke about hourglasses");

        // Bot reply
        var reply = chatService.getChatMessageContentsAsync(chatHistory, kernel, null).block();
        System.out.println(reply);
    }
}
