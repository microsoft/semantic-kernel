package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;

import java.io.IOException;

public class Example05_UsingThePlanner {

    public static SequentialPlanner getPlanner(Kernel kernel) {
        kernel.importSkill("SummarizeSkill", KernelExtensions.importSemanticSkillFromDirectory(
                "samples/skills", "SummarizeSkill"));
        kernel.importSkill("WriterSkill", KernelExtensions.importSemanticSkillFromDirectory(
                "samples/skills", "WriterSkill"));

        return new SequentialPlanner(kernel, null, null);
    }

    public static void run (Config.ClientType clientType) throws IOException {
        Kernel kernel = Example00_GettingStarted.getKernel(clientType.getClient());

        SequentialPlanner planner = getPlanner(kernel);
        System.out.println(planner.createPlanAsync(
                "Write a poem about John Doe, then translate it into Italian.")
                .block().getResult());

        // TODO: execute the plan
    }

    public static void main(String[] args) throws IOException {
        // Send one of Config.ClientType.OPEN_AI or Config.ClientType.AZURE_OPEN_AI
        run(Config.ClientType.OPEN_AI);
    }

}
