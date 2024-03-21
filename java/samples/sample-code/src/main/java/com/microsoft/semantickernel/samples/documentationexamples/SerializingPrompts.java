// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

public class SerializingPrompts {
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID",
        "gpt-35-turbo-2");

    public static void main(String[] args) {
        System.out.println("======== Serializing Prompts ========");
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

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, ChatCompletionService.builder()
                .withModelId(MODEL_ID)
                .withOpenAIAsyncClient(client)
                .build())
            .build();

        // Load prompts
        // This part is omitted as it requires a specific implementation to load prompts from a directory

        // Load prompt from YAML
        // This part is omitted as it requires a specific implementation to load prompts from a YAML file

        // Create choices
        List<String> choices = Arrays.asList("ContinueConversation", "EndConversation");

        // Create few-shot examples
        // This part is omitted as it requires a specific implementation to create few-shot examples

        // Create chat history
        // This part is omitted as it requires a specific implementation to create chat history

        // Start the chat loop
        Scanner scanner = new Scanner(System.in);
        System.out.print("User > ");
        String userInput;
        while (!(userInput = scanner.nextLine()).isEmpty()) {
            // Invoke handlebars prompt
            // This part is omitted as it requires a specific implementation to invoke a prompt

            // End the chat if the intent is "Stop"
            // This part is omitted as it requires a specific implementation to handle the intent

            // Get chat response
            // This part is omitted as it requires a specific implementation to get the chat response

            // Stream the response
            // This part is omitted as it requires a specific implementation to stream the response

            // Append to history
            // This part is omitted as it requires a specific implementation to append to the history

            // Get user input again
            System.out.print("User > ");
        }
    }
}