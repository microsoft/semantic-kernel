// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.chatcompletion;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.syntaxexamples.Example17ChatGPTTest;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuples;

public class OpenAIChatCompletionTest {

    @Test
    public void chatCompletionCanBeUsedAsATextCompletion() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(Tuples.of("Run completion", "A-RESULT"));
        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.chatCompletion()
                                        .withOpenAIClient(client)
                                        .withModelId("gpt-3.5-turbo-0301")
                                        .build())
                        .build();

        TextCompletion textCompletion = kernel.getService(null, TextCompletion.class);

        List<String> result =
                textCompletion
                        .completeAsync("Run completion", new CompletionRequestSettings())
                        .block();

        Assertions.assertEquals(1, result.size());
        Assertions.assertEquals("A-RESULT", result.get(0));
    }

    @Test
    public void azureOpenAIChatSampleAsync() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(Tuples.of("Today is", "A-RESULT"));

        String message = "Hi, I'm looking for book suggestions";
        Example17ChatGPTTest.mockResponse(client, message, "1st response");

        String result = getRunExample(client, message);
        Assertions.assertEquals("1st response", result);
    }

    private static String getRunExample(OpenAIAsyncClient client, String message) {
        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.chatCompletion()
                                        .withOpenAIClient(client)
                                        .withModelId("gpt-3.5-turbo-0301")
                                        .build())
                        .build();

        ChatCompletion<OpenAIChatHistory> chatGPT = kernel.getService(null, ChatCompletion.class);

        OpenAIChatHistory chatHistory =
                chatGPT.createNewChat("You are a librarian, expert about books");

        // First user message
        chatHistory.addUserMessage(message);
        ChatHistory.Message createdMessage = chatHistory.getLastMessage().get();
        Assertions.assertEquals(ChatHistory.AuthorRoles.User, createdMessage.getAuthorRoles());
        Assertions.assertEquals(message, createdMessage.getContent());

        // First bot assistant message
        return chatGPT.generateMessageAsync(chatHistory, null).block();
    }

    @Test
    public void emptyResponseThrowsError() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(Tuples.of("Today is", "A-RESULT"));

        String message = "Hi, I'm looking for book suggestions";

        ChatCompletions completion = Mockito.mock(ChatCompletions.class);
        Mockito.when(completion.getChoices()).thenReturn(new ArrayList<>());

        Mockito.when(
                        client.getChatCompletions(
                                Mockito.any(),
                                Mockito.<ChatCompletionsOptions>argThat(
                                        msg -> {
                                            return msg != null
                                                    && msg.getMessages()
                                                            .get(msg.getMessages().size() - 1)
                                                            .getContent()
                                                            .equals(message);
                                        })))
                .thenReturn(Mono.just(completion));

        Assertions.assertThrows(AIException.class, () -> getRunExample(client, message));
    }
}
