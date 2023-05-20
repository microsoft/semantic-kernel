package com.microsoft.semantickernel;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.function.Function;

/**
 * Chatbot using context variables
 *
 * Context Variables object which in this demo functions similarly as a key-value store that you can use when running the kernel.
 * The context is local (i.e. in your computer's RAM) and not persisted anywhere beyond the life of the JVM execution.
 */
public class Example04ContextVariablesChat {
  public static void startChat (Kernel kernel)
      throws ExecutionException, InterruptedException, TimeoutException {
    String prompt ="""
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
                            2000,
                            new ArrayList<>()
                    ));

    CompletionSKContext readOnlySkContext = chat.buildContext();

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

  private static Mono<CompletionSKContext> chat(
      String input, CompletionSKFunction chat, CompletionSKContext context)
      throws ExecutionException, InterruptedException, TimeoutException {
    context = context.setVariable("user_input", input);

    System.out.println("User: " + input);

    CompletionSKContext finalContext = context;
    return chat.invokeAsync(context, null)
        .map(
            result -> {
              System.out.println("Bot: " + result.getResult() + "\n");

              String existingHistoy =
                  finalContext.getVariables().asMap().get("history");
              if (existingHistoy == null) {
                existingHistoy = "";
              }
              existingHistoy +=
                  "\nUser: " + input + "\nChatBot: " + result.getResult() + "\n";
              return finalContext.setVariable("history", existingHistoy);
            });
  }

  private static Function<CompletionSKContext, Mono<CompletionSKContext>> chat(
      String input, CompletionSKFunction chat) {
    return (context) -> {
      try {
        return chat(input, chat, context);
      } catch (ExecutionException | InterruptedException | TimeoutException e) {
        return Mono.error(e);
      }
    };
  }

  public static void run (boolean useAzureOpenAI)
      throws ExecutionException, InterruptedException, TimeoutException {
    OpenAIAsyncClient client = Config.getClient(useAzureOpenAI);
    Kernel kernel = Example00GettingStarted.getKernel(client);

    startChat(kernel);
  }

  public static void main (String[] args)
      throws ExecutionException, InterruptedException, TimeoutException {
    run(false);
  }
}
