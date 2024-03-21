// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import java.io.InputStream;
import java.util.Scanner;

public class SerializingPrompts {

    public static InputStream INPUT = System.in;

    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-3.5-turbo");

    public static void main(String[] args) {

        System.out.println("======== Serializing ========");

        OpenAIAsyncClient client;

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

        var chatCompletionService = ChatCompletionService.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        var conversationSummaryPlugin = KernelPluginFactory
            .createFromObject(new ConversationSummaryPlugin(), "ConversationSummaryPlugin");

        var chatPlugin = KernelPluginFactory.importPluginFromResourcesDirectory(
            "Plugins",
            "Prompts",
            "Chat",
            null,
            String.class);

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(conversationSummaryPlugin)
            .withPlugin(chatPlugin)
            .build();

        ChatHistory chatHistory = new ChatHistory();

        chatCompletionService
            .getChatMessageContentsAsync(
                chatHistory,
                kernel,
                null)
            .block();

        Scanner scanner = new Scanner(INPUT);

        ChatHistory history = new ChatHistory(
            "This example is a chat bot that answers questions. Ask a question to get started. Type 'exit' to quit.");

        System.out.println(
            "This example is a chat bot that answers questions. Ask a question to get started. Type 'exit' to quit.");

        // Start the chat loop
        while (true) {
            // Get user input
            System.out.println("User > ");
            var request = scanner.nextLine();
            if ("exit".equalsIgnoreCase(request)) {
                break;
            }

            var chatResult = kernel
                .invokeAsync(chatPlugin.get("chat"))
                .withArguments(
                    KernelFunctionArguments.builder()
                        .withVariable("request", request)
                        .withVariable("history", history)
                        .build())
                .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
                .block();

            String message = chatResult.getResult();
            System.out.println("Assistant: " + message);
            System.out.println();

            // Append to history
            history.addUserMessage(request);
            history.addAssistantMessage(message);
        }
    }
}