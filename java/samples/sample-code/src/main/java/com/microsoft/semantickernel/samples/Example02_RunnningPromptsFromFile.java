///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.6-alpha
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java,Example00_GettingStarted.java
package com.microsoft.semantickernel.samples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.samples.syntaxexamples.SampleSkillsUtil;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import java.io.IOException;

/**
 * Using Semantic Functions stored on disk
 *
 * A Semantic Skill is a collection of Semantic Functions, where each function
 * is defined with natural language that can be provided with a text file.
 * Refer to our <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/main/docs/GLOSSARY.md">glossary</a>
 * for an in-depth guide to the terms.
 *
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

    public static void run(Config.ClientType clientType) throws IOException {
        Kernel kernel = Example00_GettingStarted.getKernel(clientType.getClient());
        CompletionSKFunction jokeFunction = getJokeFunction(kernel);

        System.out.println(jokeFunction.invokeAsync("time travel to dinosaur age").block().getResult());
    }

    public static void main(String args[]) throws IOException {
        // Send one of Config.ClientType.OPEN_AI or Config.ClientType.AZURE_OPEN_AI
        run(Config.ClientType.OPEN_AI);
    }
}
