package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.syntaxexamples.SampleSkillsUtil;

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
