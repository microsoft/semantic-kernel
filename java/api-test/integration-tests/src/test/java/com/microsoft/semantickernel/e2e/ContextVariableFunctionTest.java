// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

public class ContextVariableFunctionTest extends AbstractKernelTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(ContextVariableFunctionTest.class);

    public static void main(String[] args)
            throws ExecutionException,
                    InterruptedException,
                    TimeoutException,
                    ConfigurationException {
        new ContextVariableFunctionTest().runContextVariableTest();
    }

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void runContextVariableTest()
            throws ExecutionException,
                    InterruptedException,
                    TimeoutException,
                    ConfigurationException {
        Kernel kernel = buildTextCompletionKernel();

        String prompt =
                """
                        ChatBot can have a conversation with you about any topic.
                        It can give explicit instructions or say 'I don't know' if it does not have an answer.

                        {{$history}}
                        User: {{$user_input}}
                        ChatBot:\s""";

        CompletionSKFunction chat =
                kernel.getSemanticFunctionBuilder()
                        .withPromptTemplate(prompt)
                        .withFunctionName("ChatBot")
                        .withCompletionConfig(
                                new PromptTemplateConfig.CompletionConfig(0.7, 0.5, 0, 0, 2000))
                        .build();

        SKContext readOnlySkContext = SKBuilders.context().withKernel(kernel).build();

        chat("Hi, I'm looking for book suggestions?", chat, readOnlySkContext)
                .flatMap(
                        chat(
                                "I love history and philosophy, I'd like to learn something new"
                                        + " about Greece, any suggestion?",
                                chat))
                .flatMap(chat("that sounds interesting, what is it about?", chat))
                .flatMap(
                        chat(
                                "if I read that book, what exactly will I learn about Greece"
                                        + " history?",
                                chat))
                .flatMap(
                        chat("could you list some more books I could read about this topic?", chat))
                .block();
    }

    private Function<SKContext, Mono<SKContext>> chat(String input, CompletionSKFunction chat) {
        return (context) -> {
            try {
                return chat(input, chat, context);
            } catch (ExecutionException | InterruptedException | TimeoutException e) {
                return Mono.error(e);
            }
        };
    }

    private Mono<SKContext> chat(String input, CompletionSKFunction chat, SKContext context)
            throws ExecutionException, InterruptedException, TimeoutException {
        context = context.setVariable("user_input", input);

        LOGGER.info("User:\n" + input);

        SKContext finalContext = context;
        return chat.invokeAsync(context, null)
                .map(
                        result -> {
                            LOGGER.info("Bot:\n\t\t" + result.getResult());

                            String existingHistoy = finalContext.getVariables().get("history");
                            if (existingHistoy == null) {
                                existingHistoy = "";
                            }
                            existingHistoy +=
                                    "\nUser: " + input + "\nChatBot: " + result.getResult() + "\n";
                            return finalContext.setVariable("history", existingHistoy);
                        });
    }
}
