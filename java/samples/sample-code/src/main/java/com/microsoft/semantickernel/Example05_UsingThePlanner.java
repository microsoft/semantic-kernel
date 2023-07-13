package com.microsoft.semantickernel;

import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.syntaxexamples.SampleSkillsUtil;

import java.io.IOException;

public class Example05_UsingThePlanner {

    public static SequentialPlanner getPlanner(Kernel kernel) {
        kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", SampleSkillsUtil.detectSkillDirLocation(), "WriterSkill");

        return new SequentialPlanner(kernel, null, null);
    }

    public static void run(Config.ClientType clientType) throws IOException {
        Kernel kernel = Example00_GettingStarted.getKernel(clientType.getClient());

        SequentialPlanner planner = getPlanner(kernel);
        System.out.println(planner.createPlanAsync(
                "Write a poem about John Doe, then translate it into Italian.")
                .block().invokeAsync().block().getResult());

        // TODO: execute the plan
    }

    public static void main(String[] args) throws IOException {
        // Send one of Config.ClientType.OPEN_AI or Config.ClientType.AZURE_OPEN_AI
        run(Config.ClientType.OPEN_AI);
    }

}
