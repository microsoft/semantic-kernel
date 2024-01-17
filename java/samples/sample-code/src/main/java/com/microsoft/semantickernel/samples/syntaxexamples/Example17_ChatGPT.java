package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;

public class Example17_ChatGPT {

    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
            System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    public static void main(String[] args) {
        System.out.println("======== Open AI - ChatGPT ========");

        OpenAIAsyncClient client;

        if (USE_AZURE_CLIENT) {
            client = new OpenAIClientBuilder()
                    .credential(new AzureKeyCredential(CLIENT_KEY))
                    .endpoint(CLIENT_ENDPOINT)
                    .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                    .credential(new KeyCredential(CLIENT_KEY))
                    .buildAsyncClient();
        }

        ChatCompletionService chatGPT = OpenAIChatCompletion.builder()
                .withModelId("gpt-35-turbo")
                .withOpenAIAsyncClient(client)
                .build();

        System.out.println("Chat content:");
        System.out.println("------------------------");

        ChatHistory chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.addUserMessage("Hi, I'm looking for book suggestions");
        messageOutput(chatHistory);

        GPTReply(chatGPT, chatHistory);
        messageOutput(chatHistory);

        chatHistory.addUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        messageOutput(chatHistory);

        GPTReply(chatGPT, chatHistory);
        messageOutput(chatHistory);
    }

    private static void messageOutput(ChatHistory chatHistory) {
        var message = chatHistory.getLastMessage().get();
        System.out.println(message.getAuthorRole() + ": " + message.getContent());
        System.out.println("------------------------");
    }

    private static void GPTReply(ChatCompletionService chatGPT, ChatHistory chatHistory) {
        var reply = chatGPT.getChatMessageContentsAsync(chatHistory, null, null)
                .block();

        StringBuilder message = new StringBuilder();
        reply.forEach(chatMessageContent -> message.append(chatMessageContent.getContent()));
        chatHistory.addAssistantMessage(message.toString());
    }
}
