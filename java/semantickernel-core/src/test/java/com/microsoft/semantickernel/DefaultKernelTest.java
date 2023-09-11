// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatMessage;
import com.azure.ai.openai.models.Choice;
import com.azure.ai.openai.models.Completions;
import com.azure.ai.openai.models.CompletionsOptions;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatcher;
import org.mockito.Mockito;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuple3;
import reactor.util.function.Tuples;

public class DefaultKernelTest {

    @Test
    void contextVariableTest() {

        String model = "a-model";

        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of("A", "a"), Tuples.of("user: Aauser: B", "b"));

        Kernel kernel = buildKernel(model, client);

        String prompt = "{{$history}}user: {{$user_input}}\n";

        CompletionSKFunction chat =
                kernel.getSemanticFunctionBuilder()
                        .withKernel(kernel)
                        .withPromptTemplate(prompt)
                        .withFunctionName("ChatBot")
                        .withCompletionConfig(
                                new PromptTemplateConfig.CompletionConfig(0.7, 0.5, 0, 0, 2000))
                        .build();

        SKContext readOnlySkContext =
                SKBuilders.context()
                        .withKernel(kernel)
                        .build()
                        .setVariable("history", "")
                        .setVariable("user_input", "A");

        SKContext result = chat.invokeAsync(readOnlySkContext, null).block();

        if (result == null) {
            Assertions.fail();
        }

        Assertions.assertEquals("a", result.getResult());

        result =
                result.appendToVariable("history", "user: A" + result.getResult())
                        .setVariable("user_input", "B");

        result = chat.invokeAsync(result, null).block();
        if (result == null) {
            Assertions.fail();
        }
        Assertions.assertEquals("b", result.getResult());
    }

    @Test
    void tellAJoke() {
        String expectedResponse = "a result joke";
        OpenAIAsyncClient client = mockCompletionOpenAIAsyncClient("WRITE", expectedResponse);
        String model = "a-model-name";
        Kernel kernel = buildKernel(model, client);

        CompletionSKFunction function =
                kernel.importSkillFromDirectory("FunSkill", "../../samples/skills")
                        .getFunction("joke", CompletionSKFunction.class);

        Mono<SKContext> mono = function.invokeAsync("time travel to dinosaur age");
        SKContext result = mono.block();

        String expected =
                "WRITE EXACTLY ONE JOKE or HUMOROUS STORY ABOUT THE TOPIC BELOW\n"
                        + "\n"
                        + "JOKE MUST BE:\n"
                        + "- G RATED\n"
                        + "- WORKPLACE/FAMILY SAFE\n"
                        + "NO SEXISM, RACISM OR OTHER BIAS/BIGOTRY\n"
                        + "\n"
                        + "BE CREATIVE AND FUNNY. I WANT TO LAUGH.\n"
                        + "\n"
                        + "+++++\n"
                        + "\n"
                        + "time travel to dinosaur age\n"
                        + "+++++\n";

        assertCompletionsWasCalledWithModelAndText(client, model, expected);

        assertTheResultEquals(result, expectedResponse);
    }

    public static Kernel buildKernel(String model, OpenAIAsyncClient client) {
        TextCompletion textCompletion = new OpenAITextCompletion(client, model);

        return SKBuilders.kernel().withDefaultAIService(textCompletion).build();
    }

    private static OpenAIAsyncClient mockCompletionOpenAIAsyncClient(String arg, String response) {
        List<Tuple2<String, String>> responses =
                Collections.singletonList(Tuples.of(arg, response));

        return mockCompletionOpenAIAsyncClient(responses.toArray(new Tuple2[0]));
    }

    /*
     * Mocks a Text Completion client where if the prompt matches it will return the
     * first arg it will return the response,
     * i.e:
     *
     * mockCompletionOpenAIAsyncClient(
     * List.<>of(
     * Tuples.of("Tell me a joke", "This is a joke")
     * )
     * );
     *
     * This if the client is prompted with "Tell me a joke", the mocked client would
     * respond with "This is a joke"
     */
    public static OpenAIAsyncClient mockCompletionOpenAIAsyncClient(
            Tuple2<String, String>... responses) {

        List<Tuple3<ArgumentMatcher<String>, String, Consumer<String>>> matchers =
                Arrays.stream(responses)
                        .map(
                                response ->
                                        Tuples
                                                .<ArgumentMatcher<String>, String, Consumer<String>>
                                                        of(
                                                                arg ->
                                                                        arg.contains(
                                                                                response.getT1()),
                                                                response.getT2(),
                                                                (arg) -> {}))
                        .collect(Collectors.toList());

        return DefaultKernelTest.mockCompletionOpenAIAsyncClientMatchAndAssert(
                matchers.toArray(new Tuple3[0]));
    }

    public static OpenAIAsyncClient mockCompletionOpenAIAsyncClientMatch(
            Tuple2<ArgumentMatcher<String>, String>... responses) {

        Tuple3[] withAssert =
                Arrays.stream(responses)
                        .map(
                                spec ->
                                        Tuples
                                                .<ArgumentMatcher<String>, String, Consumer<String>>
                                                        of(spec.getT1(), spec.getT2(), arg -> {}))
                        .collect(Collectors.toList())
                        .toArray(new Tuple3[0]);

        return mockCompletionOpenAIAsyncClientMatchAndAssert(withAssert);
    }

    public static OpenAIAsyncClient mockCompletionOpenAIAsyncClientMatchAndAssert(
            Tuple3<ArgumentMatcher<String>, String, Consumer<String>>... responses) {
        OpenAIAsyncClient openAIAsyncClient = Mockito.mock(OpenAIAsyncClient.class);

        for (Tuple3<ArgumentMatcher<String>, String, Consumer<String>> response : responses) {
            mockChatCompletionResponse(openAIAsyncClient, response);
            mockChatCompletionResponseStreaming(openAIAsyncClient, response);
            mockTextCompletionResponse(openAIAsyncClient, response);
            mockTextCompletionResponseStreaming(openAIAsyncClient, response);
        }
        return openAIAsyncClient;
    }

    private static void mockTextCompletionResponse(
            OpenAIAsyncClient openAIAsyncClient,
            Tuple3<ArgumentMatcher<String>, String, Consumer<String>> response) {
        Choice choice = Mockito.mock(Choice.class);
        Mockito.when(choice.getText()).thenReturn(response.getT2());
        Completions completions = Mockito.mock(Completions.class);
        Mockito.when(completions.getChoices()).thenReturn(Collections.singletonList(choice));
        Mockito.when(completions.getId()).thenReturn(UUID.randomUUID().toString());

        Mockito.when(
                        openAIAsyncClient.getCompletions(
                                Mockito.any(String.class),
                                Mockito.<CompletionsOptions>argThat(
                                        it -> response.getT1().matches(it.getPrompt().get(0)))))
                .then(
                        (arg) -> {
                            response.getT3()
                                    .accept(
                                            ((CompletionsOptions) arg.getArgument(1))
                                                    .getPrompt()
                                                    .get(0));
                            return Mono.just(completions);
                        })
                .thenReturn(Mono.just(completions));

        Mockito.when(
                        openAIAsyncClient.getCompletions(
                                Mockito.any(String.class),
                                Mockito.<String>argThat(it -> response.getT1().matches(it))))
                .then(
                        (arg) -> {
                            response.getT3()
                                    .accept(
                                            ((CompletionsOptions) arg.getArgument(1))
                                                    .getPrompt()
                                                    .get(0));
                            return Mono.just(completions);
                        })
                .thenReturn(Mono.just(completions));
    }

    private static void mockTextCompletionResponseStreaming(
            OpenAIAsyncClient openAIAsyncClient,
            Tuple3<ArgumentMatcher<String>, String, Consumer<String>> response) {
        Choice choice = Mockito.mock(Choice.class);
        Mockito.when(choice.getText()).thenReturn(response.getT2());
        Completions completions = Mockito.mock(Completions.class);
        Mockito.when(completions.getChoices()).thenReturn(Collections.singletonList(choice));
        Mockito.when(completions.getId()).thenReturn(UUID.randomUUID().toString());

        Mockito.when(
                        openAIAsyncClient.getCompletionsStream(
                                Mockito.any(String.class),
                                Mockito.argThat(
                                        it -> response.getT1().matches(it.getPrompt().get(0)))))
                .then(
                        (arg) -> {
                            response.getT3()
                                    .accept(
                                            ((CompletionsOptions) arg.getArgument(1))
                                                    .getPrompt()
                                                    .get(0));
                            return Flux.just(completions);
                        })
                .thenReturn(Flux.just(completions));

        Mockito.when(
                        openAIAsyncClient.getCompletionsStream(
                                Mockito.any(String.class),
                                Mockito.argThat(
                                        it ->
                                                response.getT1()
                                                        .matches(
                                                                it.getPrompt()
                                                                        .get(
                                                                                it.getPrompt()
                                                                                                .size()
                                                                                        - 1)))))
                .then(
                        (arg) -> {
                            response.getT3()
                                    .accept(
                                            ((CompletionsOptions) arg.getArgument(1))
                                                    .getPrompt()
                                                    .get(0));
                            return Flux.just(completions);
                        })
                .thenReturn(Flux.just(completions));
    }

    private static void mockChatCompletionResponse(
            OpenAIAsyncClient openAIAsyncClient,
            Tuple3<ArgumentMatcher<String>, String, Consumer<String>> response) {
        ChatMessage message = Mockito.mock(ChatMessage.class);
        Mockito.when(message.getContent()).thenReturn(response.getT2());
        ChatChoice chatChoice = Mockito.mock(ChatChoice.class);
        Mockito.when(chatChoice.getMessage()).thenReturn(message);
        ChatCompletions chatCompletions = Mockito.mock(ChatCompletions.class);

        Mockito.when(chatCompletions.getChoices())
                .thenReturn(Collections.singletonList(chatChoice));
        Mockito.when(chatCompletions.getId()).thenReturn(UUID.randomUUID().toString());

        ArgumentMatcher<ChatCompletionsOptions> completionMatcher =
                chatCompletionsOptions ->
                        response.getT1()
                                .matches(
                                        chatCompletionsOptions.getMessages().stream()
                                                .map(ChatMessage::getContent)
                                                .collect(Collectors.joining("\n")));

        Mockito.when(
                        openAIAsyncClient.getChatCompletions(
                                Mockito.any(String.class), Mockito.argThat(completionMatcher)))
                .thenReturn(Mono.just(chatCompletions));
    }

    private static void mockChatCompletionResponseStreaming(
            OpenAIAsyncClient openAIAsyncClient,
            Tuple3<ArgumentMatcher<String>, String, Consumer<String>> response) {

        String responseStr = response.getT2();

        String[] responseArray =
                new String[] {
                    responseStr.substring(0, responseStr.length() / 2),
                    responseStr.substring(responseStr.length() / 2)
                };

        List<ChatChoice> choices =
                Arrays.stream(responseArray)
                        .map(
                                r -> {
                                    ChatMessage message = Mockito.mock(ChatMessage.class);
                                    Mockito.when(message.getContent()).thenReturn(r);
                                    ChatChoice chatChoice = Mockito.mock(ChatChoice.class);
                                    Mockito.when(chatChoice.getDelta()).thenReturn(message);
                                    Mockito.when(chatChoice.getMessage()).thenReturn(message);
                                    return chatChoice;
                                })
                        .collect(Collectors.toList());

        ChatCompletions chatCompletions = Mockito.mock(ChatCompletions.class);
        Mockito.when(chatCompletions.getChoices()).thenReturn(choices);
        Mockito.when(chatCompletions.getId()).thenReturn(UUID.randomUUID().toString());

        ArgumentMatcher<ChatCompletionsOptions> completionMatcher =
                chatCompletionsOptions ->
                        response.getT1()
                                .matches(
                                        chatCompletionsOptions.getMessages().stream()
                                                .map(ChatMessage::getContent)
                                                .collect(Collectors.joining("\n")));

        Mockito.when(
                        openAIAsyncClient.getChatCompletionsStream(
                                Mockito.any(String.class), Mockito.argThat(completionMatcher)))
                .thenReturn(Flux.just(chatCompletions));
    }

    @Test
    void inlineFunctionTest() {

        String model = "a-model";

        String expectedResponse = "foo";
        OpenAIAsyncClient openAIAsyncClient =
                mockCompletionOpenAIAsyncClient("block", expectedResponse);

        Kernel kernel = buildKernel(model, openAIAsyncClient);

        String text = "A block of text\n";

        String prompt = "{{$input}}\n" + "Summarize the content above.";

        CompletionSKFunction summarize =
                SKBuilders.completionFunctions()
                        .withKernel(kernel)
                        .withPromptTemplate(prompt)
                        .withFunctionName("summarize")
                        .withCompletionConfig(
                                new PromptTemplateConfig.CompletionConfig(0.2, 0.5, 0, 0, 2000))
                        .build();

        Mono<SKContext> mono = summarize.invokeAsync(text);
        SKContext result = mono.block();

        String expected = "A block of text\n\nSummarize the content above.";

        assertCompletionsWasCalledWithModelAndText(openAIAsyncClient, model, expected);
        assertTheResultEquals(result, expectedResponse);
    }

    private void assertTheResultEquals(SKContext result, String expected) {
        Assertions.assertEquals(expected, result.getResult());
    }

    private static void assertCompletionsWasCalledWithModelAndText(
            OpenAIAsyncClient openAIAsyncClient, String model, String expected) {

        Mockito.verify(openAIAsyncClient, Mockito.times(1))
                .getCompletionsStream(
                        Mockito.matches(model),
                        Mockito.argThat(
                                completionsOptions ->
                                        completionsOptions.getPrompt().size() == 1
                                                && completionsOptions
                                                        .getPrompt()
                                                        .get(0)
                                                        .equals(expected)));
    }
}
