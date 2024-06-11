// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.chatcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.microsoft.semantickernel.aiservices.google.chatcompletion.GeminiChatCompletion;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;

public class Example96_GeminiChatCompletion {
    private static final String PROJECT_ID = System.getenv("PROJECT_ID");
    private static final String LOCATION = System.getenv("LOCATION");
    private static final String MODEL_ID = System.getenv("GEMINI_MODEL_ID");

    public static void main(String[] args) {
        // Authenticate with Google Cloud running:
        // gcloud config set project PROJECT_ID
        // gcloud auth login ACCOUNT
        //
        // Or if you want to use an API key follow:
        // https://cloud.google.com/docs/authentication/api-keys#using-with-client-libs

        VertexAI client = new VertexAI(PROJECT_ID, LOCATION);

        ChatCompletionService geminiChat = GeminiChatCompletion.builder()
            .withVertexAIClient(client)
            .withModelId(MODEL_ID)
            .build();

        System.out.println("Chat content:");
        System.out.println("------------------------");

        ChatHistory chatHistory = new ChatHistory();

        // First user message
        chatHistory.addUserMessage("Hi, I'm looking for book suggestions");
        messageOutput(chatHistory);

        reply(geminiChat, chatHistory);
        messageOutput(chatHistory);

        chatHistory.addUserMessage(
            "I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        messageOutput(chatHistory);

        reply(geminiChat, chatHistory);
        messageOutput(chatHistory);
    }

    private static void messageOutput(ChatHistory chatHistory) {
        var message = chatHistory.getLastMessage().get();
        System.out.println(message.getAuthorRole() + ": " + message.getContent());
        System.out.println("------------------------");
    }

    private static void reply(ChatCompletionService geminiChat, ChatHistory chatHistory) {
        var reply = geminiChat.getChatMessageContentsAsync(chatHistory, null, null)
            .block();

        StringBuilder message = new StringBuilder();
        reply.forEach(chatMessageContent -> message.append(chatMessageContent.getContent()));
        chatHistory.addAssistantMessage(message.toString());
    }
}
