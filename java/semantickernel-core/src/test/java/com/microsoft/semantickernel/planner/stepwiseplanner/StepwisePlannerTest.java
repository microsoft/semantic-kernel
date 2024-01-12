// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.stepwiseplanner;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatChoice;
import com.azure.ai.openai.models.ChatCompletions;
import com.azure.ai.openai.models.ChatMessage;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.coreskills.TimeSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.mockito.stubbing.Answer;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class StepwisePlannerTest {

    @Test
    public void runChatCompletion() {
        Kernel kernel = getKernel();
        SKContext result =
                runWithQuestion(kernel, "What year is the first world cup divided by 2").block();

        Assertions.assertEquals(
                "The year of the first world cup is 1930, and when divided by 2, the result is"
                        + " 965.",
                result.getResult());
    }

    public static class WebSearchEngineSkill {

        @DefineSKFunction(description = "Perform a web search.", name = "search")
        public Mono<String> search(
                @SKFunctionParameters(description = "Text to search for", name = "query")
                        String input,
                @SKFunctionParameters(
                                description = "Number of results",
                                name = "count",
                                defaultValue = "1",
                                type = Integer.class)
                        Integer count,
                @SKFunctionParameters(
                                description = "Number of results to skip",
                                name = "offset",
                                defaultValue = "0",
                                type = Integer.class)
                        Integer offset) {
            return Mono.just("1930");
        }
    }

    public static class AdvancedCalculator {
        @DefineSKFunction(
                description = "Useful for getting the result of a non-trivial math expression.",
                name = "Calculator")
        public Mono<String> Calculator(
                @SKFunctionParameters(
                                description =
                                        "A valid mathematical expression that could be executed by"
                                                + " a calculator capable of more advanced math"
                                                + " functions like sin/cosine/floor.",
                                name = "input")
                        String input) {
            return Mono.just("40");
        }
    }

    private static Mono<SKContext> runWithQuestion(Kernel kernel, String question) {
        WebSearchEngineSkill webSearchEngineSkill = new WebSearchEngineSkill();

        kernel.importSkill(webSearchEngineSkill, "WebSearch");
        kernel.importSkill(new AdvancedCalculator(), "AdvancedCalculator");
        kernel.importSkill(new TimeSkill(), "time");

        System.out.println("*****************************************************");
        System.out.println("Question: " + question);

        StepwisePlanner planner = new DefaultStepwisePlanner(kernel, null, null, null);

        Plan plan = planner.createPlan(question);

        return plan.invokeAsync(SKBuilders.context().withKernel(kernel).build());
    }

    private static Kernel getKernel() {
        OpenAIAsyncClient client = Mockito.mock(OpenAIAsyncClient.class);

        AtomicInteger callCount = new AtomicInteger(0);

        Mockito.when(client.getChatCompletionsStream(Mockito.any(), Mockito.any()))
                .then(
                        (Answer<Flux<ChatCompletions>>)
                                invocationOnMock -> {
                                    int index = callCount.incrementAndGet();

                                    String response =
                                            EmbeddedResourceLoader.readFile(
                                                    "response" + index + ".txt",
                                                    StepwisePlannerTest.class);

                                    ChatMessage chatMessage = Mockito.mock(ChatMessage.class);
                                    Mockito.when(chatMessage.getContent()).thenReturn(response);

                                    ChatChoice chatChoice = Mockito.mock(ChatChoice.class);
                                    Mockito.when(chatChoice.getMessage()).thenReturn(chatMessage);
                                    Mockito.when(chatChoice.getDelta()).thenReturn(chatMessage);

                                    ChatCompletions chatCompletion =
                                            Mockito.mock(ChatCompletions.class);
                                    Mockito.when(chatCompletion.getChoices())
                                            .thenReturn(Arrays.asList(chatChoice));
                                    Mockito.when(chatCompletion.getId()).thenReturn("foo");

                                    return Flux.just(chatCompletion);
                                });

        TextCompletion textCompletion =
                SKBuilders.chatCompletion()
                        .withOpenAIClient(client)
                        .withModelId("gpt-35-turbo")
                        .build();

        return SKBuilders.kernel().withDefaultAIService(textCompletion).build();
    }
}
