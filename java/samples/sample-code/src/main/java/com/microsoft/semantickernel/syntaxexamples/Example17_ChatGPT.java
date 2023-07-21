// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.connectors.ai.openai.chatcompletion.OpenAIChatHistory;
import com.microsoft.semantickernel.exceptions.ConfigurationException;

import java.io.IOException;

/**
 * The following example shows how to use Semantic Kernel with OpenAI ChatGPT
 * API
 */
public class Example17_ChatGPT {

    public static void main(String[] args) throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();

        Kernel kernel = SKBuilders.kernel()
                .withKernelConfig(SKBuilders.kernelConfig()
                        .build())
                .withAIService(
                        "chat-test",
                        SKBuilders.chatCompletion().build(client, "chat-test"),
                        true,
                        ChatCompletion.class
                )
                .build();

        ChatCompletion<OpenAIChatHistory> chatGPT = kernel.getService(null, ChatCompletion.class);

        OpenAIChatHistory chatHistory = chatGPT.createNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.addUserMessage("Hi, I'm looking for book suggestions");
        messageOutputAsync(chatHistory);

        // First bot assistant message
        String reply = chatGPT.generateMessageAsync(chatHistory, null).block();
        chatHistory.addAssistantMessage(reply);
        messageOutputAsync(chatHistory);

        // Second user message
        chatHistory.addUserMessage(
                "I love history and philosophy, I'd like to learn something new about Greece, any suggestion?");
        messageOutputAsync(chatHistory);

        // Second bot assistant message
        reply = chatGPT.generateMessageAsync(chatHistory, null).block();
        chatHistory.addAssistantMessage(reply);
        messageOutputAsync(chatHistory);
    }

    private static void messageOutputAsync(ChatHistory chatHistory) {
        ChatHistory.Message message = chatHistory.getMessages().get(chatHistory.getMessages().size() - 1);

        System.out.println(message.getAuthorRoles() + ": " + message.getContent());
        System.out.println("------------------------");
    }
}
