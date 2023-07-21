package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.syntaxexamples.SampleSkillsUtil;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import java.io.IOException;

/**
 * Using Semantic Functions stored on disk
 * <p>
 * A Semantic Skill is a collection of Semantic Functions, where each function
 * is defined with natural language that can be provided with a text file.
 * Refer to our <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/main/docs/GLOSSARY.md">glossary</a>
 * for an in-depth guide to the terms.
 * <p>
 * The repository includes some examples under the <a href=
 * "https://github.com/microsoft/semantic-kernel/tree/main/samples">samples</a>
 * folder.
 */
public class Example02_RunnningPromptsFromFile {

    /**
     * Imports skill 'FunSkill' stored in the samples folder and then returns the
     * semantic function 'Joke' within it.
     *
     * @param kernel Kernel with Text Completion
     * @return Joke function
     */
    public static CompletionSKFunction getJokeFunction(Kernel kernel) {
        ReadOnlyFunctionCollection skill = kernel
                .importSkillFromDirectory("FunSkill", SampleSkillsUtil.detectSkillDirLocation(), "FunSkill");

        return skill.getFunction("Joke", CompletionSKFunction.class);
    }

    public static void run(OpenAIAsyncClient client) throws IOException {
        Kernel kernel = Example00_GettingStarted.getKernel(client);
        CompletionSKFunction jokeFunction = getJokeFunction(kernel);

        System.out.println(jokeFunction.invokeAsync("time travel to dinosaur age").block().getResult());
    }

    public static void main(String args[]) throws ConfigurationException, IOException {
        run(OpenAIClientProvider.getClient());
    }
}
