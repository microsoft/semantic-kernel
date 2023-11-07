///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.extensions:semantickernel-sequentialplanner-extension:0.2.6-alpha
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java,Example00_GettingStarted.java
package com.microsoft.semantickernel.samples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.samples.syntaxexamples.SampleSkillsUtil;

/**
 * Sequential Planner
 * <p>
 * See <a href=
 * "https://devblogs.microsoft.com/semantic-kernel/semantic-kernel-planners-sequential-planner/">
 * Semantic Kernel Planners: Sequential Planner</a>
 * <p>
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class Example05_UsingThePlanner {

    public static SequentialPlanner getPlanner(Kernel kernel) {
        kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", SampleSkillsUtil.detectSkillDirLocation(), "WriterSkill");

        return new SequentialPlanner(kernel, null, null);
    }

    public static void run(OpenAIAsyncClient client) {
        Kernel kernel = Example00_GettingStarted.getKernel(client);

        SequentialPlanner planner = getPlanner(kernel);
        System.out.println(planner.createPlanAsync(
                        "Write a poem about John Doe, then translate it into Italian.")
                .block().invokeAsync().block().getResult());

        // TODO: execute the plan
    }

    public static void main(String args[]) throws ConfigurationException {
        run(OpenAIClientProvider.getClient());
    }
}
