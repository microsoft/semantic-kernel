package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.identity.DeviceCodeCredential;
import com.azure.identity.DeviceCodeCredentialBuilder;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion.Builder;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.exceptions.ConfigurationException;

public class Example26_AADAuth {

    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    public static void main(String[] args) throws ConfigurationException {

        DeviceCodeCredential token = new DeviceCodeCredentialBuilder()
            .build();

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(token)
            .endpoint(CLIENT_ENDPOINT)
            .buildAsyncClient();

        OpenAIChatCompletion chatService = new Builder()
            .withOpenAIAsyncClient(client)
            .withModelId("gpt-35-turbo-2")
            .build();

        Kernel kernel = new DefaultKernel.Builder()
            .withDefaultAIService(OpenAIChatCompletion.class, chatService)
            .build();

        var chatHistory = new ChatHistory();

        // User message
        chatHistory.addUserMessage("Tell me a joke about hourglasses");

        // Bot reply
        var reply = chatService.getChatMessageContentsAsync(chatHistory, null, kernel).block();
        System.out.println(reply);
    }
}
