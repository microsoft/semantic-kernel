// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;


import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import reactor.core.publisher.Mono;

import java.util.function.BiFunction;

import static com.microsoft.semantickernel.chatcompletion.ChatHistory.AuthorRoles.Assistant;

/**
 * The following example shows how to use Semantic Kernel with Text Completion as streaming
 */
public class Example33_StreamingChat {
    public static void main(String[] args) throws ConfigurationException {
        StartStreamingChatAsync();
    }

    private static void StartStreamingChatAsync() throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();

        ChatCompletion chatCompletion = SKBuilders.chatCompletion().build(client, "gpt-35-turbo");

        System.out.println("Chat content:");
        System.out.println("------------------------");

        var chatHistory = chatCompletion.createNewChat("You are a librarian, expert about books");
        messageOutput(chatHistory);

        // First user message
        chatHistory.addMessage(ChatHistory.AuthorRoles.User, "Hi, I'm looking for book suggestions");
        messageOutput(chatHistory);

        // First bot assistant message
        streamMessageOutputAsync(chatCompletion, chatHistory, Assistant);

        // Second user message
        chatHistory.addMessage(ChatHistory.AuthorRoles.User, "I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        messageOutput(chatHistory);

        // Second bot assistant message
        streamMessageOutputAsync(chatCompletion, chatHistory, Assistant);
    }

    private static void streamMessageOutputAsync(ChatCompletion chatGPT, ChatHistory chatHistory, ChatHistory.AuthorRoles authorRole) {
        System.out.println(authorRole.name() + ": ");

        BiFunction<String, String, String> agg = (o, o2) -> o + o2;

        Mono<String> mono = chatGPT
                .generateMessageStream(chatHistory, null)
                .reduce("", agg);

        String fullMessage = mono.block();
        System.out.println(fullMessage);
        System.out.println("\n------------------------");
        chatHistory.addMessage(authorRole, fullMessage);
    }

    private static void messageOutput(ChatHistory chatHistory) {
        var message = chatHistory.getMessages().get(chatHistory.getMessages().size() - 1);

        System.out.println(message.getAuthorRoles().name() + " " + message.getContent());
        System.out.println("------------------------");
    }
}
