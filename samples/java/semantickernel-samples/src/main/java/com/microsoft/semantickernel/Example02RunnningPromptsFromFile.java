package com.microsoft.semantickernel;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import java.io.IOException;

/**
 * Using Semantic Functions stored on disk
 *
 * A Semantic Skill is a collection of Semantic Functions, where each function is defined with natural language that can be provided with a text file.
 * Refer to our <a href="https://github.com/microsoft/semantic-kernel/blob/main/docs/GLOSSARY.md">glossary</a> for an in-depth guide to the terms.
 *
 * The repository includes some examples under the <a href="https://github.com/microsoft/semantic-kernel/tree/main/samples">samples</a> folder.
 */
public class Example02RunnningPromptsFromFile {

  /**
   * Imports skill 'FunSkill' stored in the samples folder and then returns the semantic function 'Joke' within it.
   *
   * @param kernel  Kernel with Text Completion
   * @return        Joke function
   */
  public static CompletionSKFunction getJokeFunction(Kernel kernel) {
    ReadOnlyFunctionCollection skill = kernel
            .importSkill("FunSkill", KernelExtensions.importSemanticSkillFromDirectory(
                    "samples/skills", "FunSkill"));

    return skill.getFunction("Joke", CompletionSKFunction.class);
  }

  public static void run (boolean useAzureOpenAI) {
    OpenAIAsyncClient client = Config.getClient(useAzureOpenAI);
    Kernel kernel = Example00GettingStarted.getKernel(client);
    CompletionSKFunction jokeFunction = getJokeFunction(kernel);

    System.out.println(jokeFunction.invokeAsync("time travel to dinosaur age").block().getResult());
  }

  public static void main (String args[]) throws IOException {
    run(false);
  }
}
