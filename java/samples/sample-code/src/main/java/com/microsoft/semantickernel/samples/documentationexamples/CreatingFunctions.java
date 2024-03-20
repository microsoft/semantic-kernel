package com.microsoft.semantickernel.samples.documentationexamples;

import java.util.Scanner;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.MathPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;

public class CreatingFunctions {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID", "gpt-35-turbo-2");

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

        // Create chat history
        ChatCompletionService chat = OpenAIChatCompletion.builder()
                .withModelId(MODEL_ID)
                .withOpenAIAsyncClient(client)
                .build();

        System.out.println("Chat content:");
        System.out.println("------------------------");

        ChatHistory history = new ChatHistory();

        // Start the conversation
        System.out.print("User > ");
        Scanner scanner = new Scanner(System.in);
        String userInput;
        while (!(userInput = scanner.nextLine()).isEmpty()) {
            history.addUserMessage(userInput);

            reply(chat, history);
            messageOutput(history);
        }
    }

    private static void reply(ChatCompletionService chatGPT, ChatHistory chatHistory) {
        // Enable auto function calling
        var toolCallBehavior = ToolCallBehavior.allowAllKernelFunctions(true);

        var reply = chatGPT.getChatMessageContentsAsync(chatHistory, null, null)
                .block();

        StringBuilder message = new StringBuilder();
        reply.forEach(chatMessageContent -> message.append(chatMessageContent.getContent()));
        chatHistory.addAssistantMessage(message.toString());
    }

    private static void messageOutput(ChatHistory chatHistory) {
        var message = chatHistory.getLastMessage().get();
        System.out.println(message.getAuthorRole() + ": " + message.getContent());
        System.out.println("------------------------");
    }
}