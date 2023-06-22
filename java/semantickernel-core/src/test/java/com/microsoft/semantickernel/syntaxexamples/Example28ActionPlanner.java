// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.actionplanner.ActionPlanner;
import com.microsoft.semantickernel.planner.actionplanner.Plan;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import reactor.util.function.Tuples;

public class Example28ActionPlanner {
    @Test
    public void runActionPlan() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of("Generate a short funny", "A-RESULT"),
                        Tuples.of(
                                "plan",
                                "{\"plan\":{\n"
                                    + "\"rationale\": \"the list contains a function that can turn"
                                    + " a scenario into a short and entertaining poem\",\n"
                                    + "\"function\": \"WriterSkill.ShortPoem\",\n"
                                    + "\"parameters\": {\n"
                                    + "\"input\": \"Cleopatra\"\n"
                                    + "}}}"));

        ActionPlanner planner = createPlanner(client);
        String goal = "Write a poem about Cleopatra.";
        Plan plan = planner.createPlanAsync(goal).block();
        String planResult = plan.invokeAsync(goal).block().getResult();
        Assertions.assertEquals("A-RESULT", planResult);
    }

    @Test
    public void resultIsAnonExistentFunction() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of(
                                "plan",
                                "{\n"
                                    + "   \"plan\" : {\n"
                                    + "      \"function\" : \"TextSkill.md5sum\",\n"
                                    + "      \"parameters\" : {\n"
                                    + "         \"input\" : \"Cleopatra\"\n"
                                    + "      },\n"
                                    + "      \"rationale\" : \"the list contains a function that"
                                    + " can calculate the md5sum of a string\"\n"
                                    + "   }\n"
                                    + "}\n"));

        ActionPlanner planner = createPlanner(client);
        String goal = "Write a poem about Cleopatra.";

        Assertions.assertThrows(
                PlanningException.class,
                () -> {
                    Plan plan = planner.createPlanAsync(goal).block();
                    String planResult = plan.invokeAsync(goal).block().getResult();
                    Assertions.assertEquals("A-RESULT", planResult);
                });
    }

    private static ActionPlanner createPlanner(OpenAIAsyncClient client) {
        Kernel kernel =
                SKBuilders.kernel()
                        .setKernelConfig(
                                SKBuilders.kernelConfig()
                                        .addTextCompletionService(
                                                "text-davinci-002",
                                                kernel1 ->
                                                        SKBuilders.textCompletionService()
                                                                .build(client, "text-davinci-002"))
                                        .build())
                        .build();

        kernel.importSkillFromDirectory("SummarizeSkill", "../../samples/skills", "SummarizeSkill");

        kernel.importSkillFromDirectory("WriterSkill", "../../samples/skills", "WriterSkill");

        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        ActionPlanner planner = new ActionPlanner(kernel, null);
        return planner;
    }
}
