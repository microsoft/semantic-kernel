// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatMessage;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.connectors.ai.openai.chatcompletion.OpenAIChatHistory;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import reactor.core.publisher.Mono;
import reactor.util.function.Tuples;

import java.util.Arrays;

public class Example17ChatGPTTest {

    @Test
    public void azureOpenAIChatSampleAsync() {

        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(Tuples.of("Today is", "A-RESULT"));

        String message = "Hi, I'm looking for book suggestions";
        String secondMessage =
                "I love history and philosophy, I'd like to learn something new about Greece, any"
                        + " suggestion?";

        mockResponse(client, message, "1st response");
        mockResponse(client, secondMessage, "2nd response");

        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.chatCompletion().build(client, "gpt-3.5-turbo-0301"))
                        .build();

        ChatCompletion<OpenAIChatHistory> chatGPT = kernel.getService(null, ChatCompletion.class);

        OpenAIChatHistory chatHistory =
                chatGPT.createNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.addUserMessage(message);
        ChatHistory.Message createdMessage =
                chatHistory.getMessages().get(chatHistory.getMessages().size() - 1);
        Assertions.assertEquals(ChatHistory.AuthorRoles.User, createdMessage.getAuthorRoles());
        Assertions.assertEquals(message, createdMessage.getContent());

        // First bot assistant message
        String reply = chatGPT.generateMessageAsync(chatHistory, null).block();
        Assertions.assertEquals("1st response", reply);
        chatHistory.addAssistantMessage(reply);

        // Second user message
        chatHistory.addUserMessage(secondMessage);

        // Second bot assistant message
        reply = chatGPT.generateMessageAsync(chatHistory, null).block();
        Assertions.assertEquals("2nd response", reply);
    }

    public static void mockResponse(OpenAIAsyncClient client, String message, String response) {
        ChatMessage chatMessage = Mockito.mock(ChatMessage.class);
        ChatChoice chatChoice = Mockito.mock(ChatChoice.class);
        ChatCompletions completion = Mockito.mock(ChatCompletions.class);

        Mockito.when(completion.getChoices()).thenReturn(Arrays.asList(chatChoice));

        Mockito.when(chatChoice.getMessage()).thenReturn(chatMessage);

        Mockito.when(chatMessage.getContent()).thenReturn(response);

        Mockito.when(
                        client.getChatCompletions(
                                Mockito.any(),
                                Mockito.argThat(
                                        msg -> {
                                            return msg != null
                                                    && msg.getMessages()
                                                            .get(msg.getMessages().size() - 1)
                                                            .getContent()
                                                            .equals(message);
                                        })))
                .thenReturn(Mono.just(completion));
    }
}
