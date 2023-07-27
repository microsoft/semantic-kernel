// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.planner.actionplanner.ActionPlanner;

public class Example28_ActionPlanner {
    public static void main(String[] args) throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();

        System.out.println("======== Action Planner ========");

        var kernel = SKBuilders.kernel()
                .withDefaultAIService(SKBuilders.textCompletionService().build(client, "text-davinci-002"))
                .build();

        kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");

        kernel.importSkillFromDirectory("WriterSkill", SampleSkillsUtil.detectSkillDirLocation(), "WriterSkill");

        kernel.importSkill(new TextSkill(), "TextSkill");

        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        var planner = new ActionPlanner(kernel, null);

        // We're going to ask the planner to find a function to achieve this goal.
        var goal = "Write a poem about Cleopatra.";

        // The planner returns a plan, consisting of a single function
        // to execute and achieve the goal requested.
        var plan = planner.createPlanAsync(goal).block();

        // Show the result, which should match the given goal
        System.out.println(plan.getName());

        System.out.println(plan.invokeAsync(goal).block().getResult());

        /* Output:
         *
         * Cleopatra was a queen
         * But she didn't act like one
         * She was more like a teen

         * She was always on the scene
         * And she loved to be seen
         * But she didn't have a queenly bone in her body
         */
    }
}
