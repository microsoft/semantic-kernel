package com.microsoft.semantickernel.samples.syntaxexamples;

import com.google.cloud.vertexai.VertexAI;
import com.microsoft.semantickernel.aiservices.google.chatcompletion.VertexAIChatCompletion;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;

import java.util.List;

public class Example96_GeminiChatCompletion {

    private static final String PROJECT_ID = System.getenv("PROJECT_ID");
    private static final String LOCATION = System.getenv("LOCATION");
    private static final String MODEL_ID = System.getenv("GEMINI_MODEL_ID");

    public static void main(String[] args) {
        VertexAI client = new VertexAI(PROJECT_ID, LOCATION);

        ChatHistory chatHistory = new ChatHistory();

        ChatCompletionService chatCompletionService = VertexAIChatCompletion.builder()
                .withVertexAIClient(client)
                .withModelId(MODEL_ID)
                .build();

        List<ChatMessageContent<?>> result = chatCompletionService.getChatMessageContentsAsync(chatHistory, null, null).block();
    }
}
