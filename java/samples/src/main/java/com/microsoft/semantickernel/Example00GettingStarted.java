package com.microsoft.semantickernel;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.openai.OpenAIClientBuilder;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import reactor.core.publisher.Mono;

/**
 * Getting started
 *
 * First create a configuration file based on the examples files at the root of this module:
 *    conf.azure.properties if using Azure OpenAI
 *    conf.openai.properties if using OpenAI
 *
 * <a href="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart">Get started with Azure OpenAI</a>
 * <a href="https://openai.com/product">Get started with OpenAI</a>
 */
public class Example00GettingStarted {

  /**
   * Returns a Semantic Kernel with Text Completion.
   *
   * @param client Client that will handle requests to AzureOpenAI or OpenAI.
   * @return
   */
  public static Kernel getKernel(OpenAIAsyncClient client) {
    KernelConfig config = SKBuilders.kernelConfig()
        .addTextCompletionService("davinci", kernel -> SKBuilders.textCompletionService().build(client, "text-davinci-003"))
        .build();

    Kernel kernel = SKBuilders.kernel()
        .setKernelConfig(config)
        .build();

    return kernel;
  }

  /**
   * Imports 'FunSkill' from directory examples and runs the 'Joke' function within it.
   *
   * @param kernel Kernel with Text Completion.
   */
  public static void joke (Kernel kernel) {

    ReadOnlyFunctionCollection skill = kernel
            .importSkill("FunSkill", KernelExtensions.importSemanticSkillFromDirectory(
                    "samples/skills", "FunSkill"));

    CompletionSKFunction function = skill.getFunction("Joke",
        CompletionSKFunction.class);

    Mono<CompletionSKContext> result = function.invokeAsync("time travel to dinosaur age");

    if (result != null) {
      System.out.println(result.block().getResult());
    }
  }

  public static void run (boolean useAzureOpenAI) {
    OpenAIAsyncClient client = Config.getClient(useAzureOpenAI);
    Kernel kernel = getKernel(client);
    joke(kernel);
  }

  public static void main (String args[]) {
    // Send whether AzureOpenAI will be used. If false, OpenAI will be used.
    run(false);
  }
}
