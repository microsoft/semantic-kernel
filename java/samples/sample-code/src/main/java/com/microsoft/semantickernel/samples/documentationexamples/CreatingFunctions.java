// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.MathPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import java.util.Scanner;

public class CreatingFunctions {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID",
        "gpt-35-turbo-2");

    public static void main(String[] args) {
        System.out.println("======== Prompts ========");
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

        // <RunNativeFunction>
        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, ChatCompletionService.builder()
                .withModelId(MODEL_ID)
                .withOpenAIAsyncClient(client)
                .build())
            .withPlugin(KernelPluginFactory.createFromObject(new MathPlugin(), "MathPlugin"))
            .build();

        // Test the math plugin
        var answer = kernel
            .invokeAsync(kernel.getFunction("MathPlugin", "sqrt"))
            .withArguments(KernelFunctionArguments
                .builder()
                .withVariable("number1", 12.0)
                .build())
            .block();
        System.out.println("The square root of 12 is " + answer.getResult() + ".");
        // </RunNativeFunction>

        // Create chat history
        ChatCompletionService chat = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        System.out.println("Chat content:");
        System.out.println("------------------------");

        // <Conversation>
        ChatHistory history = new ChatHistory();

        // Start the conversation
        System.out.print("User > ");
        Scanner scanner = new Scanner(System.in);
        String userInput;
        while (!(userInput = scanner.nextLine()).isEmpty()) {
            history.addUserMessage(userInput);

            // Enable auto function calling
            var invocationContext = InvocationContext.builder()
                .withToolCallBehavior(
                    ToolCallBehavior.allowAllKernelFunctions(true))
                .build();

            // Get the response from the AI
            var reply = chat.getChatMessageContentsAsync(history, kernel, invocationContext)
                .block();

            String message = reply.get(reply.size() - 1).getContent();
            System.out.println("Assistant > " + message);

            // Add the message from the agent to the chat history
            history.addAssistantMessage(message.toString());

            // Get user input again
            System.out.print("User > ");
        }
        // </Conversation>
    }
}