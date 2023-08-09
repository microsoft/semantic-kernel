///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.6-alpha
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java,Example00_GettingStarted.java
package com.microsoft.semantickernel.samples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import reactor.core.publisher.Mono;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.function.Function;

/**
 * Chatbot using context variables
 * <p>
 * Context Variables object which in this demo functions similarly as a
 * key-value store that you can use when running the kernel.
 * The context is local (i.e. in your computer's RAM) and not persisted anywhere
 * beyond the life of the JVM execution.
 */
public class Example04_ContextVariablesChat {
    public static void startChat(Kernel kernel)
            throws ExecutionException, InterruptedException, TimeoutException {
        String prompt = """
                ChatBot can have a conversation with you about any topic.
                It can give explicit instructions or say 'I don't know' if it does not have an answer.

                {{$history}}
                User: {{$user_input}}
                ChatBot: """;

        CompletionSKFunction chat = kernel
                .getSemanticFunctionBuilder()
                .createFunction(
                        prompt,
                        "ChatBot",
                        null,
                        null,
                        new PromptTemplateConfig.CompletionConfig(
                                0.7,
                                0.5,
                                0,
                                0,
                                2000));

        SKContext readOnlySkContext = SKBuilders.context().build(kernel);

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

    private static Mono<SKContext> chat(
            String input, CompletionSKFunction chat, SKContext context)
            throws ExecutionException, InterruptedException, TimeoutException {
        context = context.setVariable("user_input", input);

        System.out.println("User: " + input);

        SKContext finalContext = context;
        return chat.invokeAsync(context, null)
                .map(
                        result -> {
                            System.out.println("Bot: " + result.getResult() + "\n");

                            String existingHistoy = finalContext.getVariables().asMap().get("history");
                            if (existingHistoy == null) {
                                existingHistoy = "";
                            }
                            existingHistoy += "\nUser: " + input + "\nChatBot: " + result.getResult() + "\n";
                            return finalContext.setVariable("history", existingHistoy);
                        });
    }

    private static Function<SKContext, Mono<SKContext>> chat(
            String input, CompletionSKFunction chat) {
        return (context) -> {
            try {
                return chat(input, chat, context);
            } catch (ExecutionException | InterruptedException | TimeoutException e) {
                return Mono.error(e);
            }
        };
    }

    public static void run(OpenAIAsyncClient client) throws ExecutionException, InterruptedException, TimeoutException {
        Kernel kernel = Example00_GettingStarted.getKernel(client);

        startChat(kernel);
    }

    public static void main(String args[]) throws ConfigurationException, ExecutionException, InterruptedException, TimeoutException {
        run(OpenAIClientProvider.getClient());
    }
}
