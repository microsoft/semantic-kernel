// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.chatcompletion.ChatHistory.AuthorRoles.Assistant;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import java.util.function.BiFunction;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuples;

public class Example33StreamingChatTest {

    @Test
    public void streamingChatAsync() {
        OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClientMatch(
                        Tuples.of(
                                request ->
                                        request.contains("You are a librarian")
                                                && !request.contains(
                                                        "I love history and philosophy"),
                                "First response"),
                        Tuples.of(
                                request ->
                                        request.contains("You are a librarian")
                                                && request.contains(
                                                        "I love history and philosophy"),
                                "Second response"));

        ChatCompletion<?> chatCompletion =
                SKBuilders.chatCompletion()
                        .withOpenAIClient(client)
                        .setModelId("gpt-35-turbo")
                        .build();

        ChatHistory chatHistory =
                chatCompletion.createNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.addMessage(
                ChatHistory.AuthorRoles.User, "Hi, I'm looking for book suggestions");

        // First bot assistant message
        String response = streamMessageOutputAsync(chatCompletion, chatHistory, Assistant).block();
        Assertions.assertEquals("First response", response);

        // Second user message
        chatHistory.addMessage(
                ChatHistory.AuthorRoles.User,
                "I love history and philosophy, I'd like to learn something new about Greece, any"
                        + " suggestion?");

        // Second bot assistant message
        response = streamMessageOutputAsync(chatCompletion, chatHistory, Assistant).block();
        Assertions.assertEquals("Second response", response);
    }

    private static Mono<String> streamMessageOutputAsync(
            ChatCompletion chatGPT, ChatHistory chatHistory, ChatHistory.AuthorRoles authorRole) {
        BiFunction<String, String, String> agg = (o, o2) -> o + o2;

        return chatGPT.generateMessageStream(chatHistory, null).reduce("", agg);
    }
}
