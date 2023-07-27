// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.actionplanner.ActionPlanner;
import com.microsoft.semantickernel.planner.actionplanner.Plan;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import reactor.util.function.Tuples;

public class Example28ActionPlannerTest {

    @Test
    public void functionsArePassedToRequest() {
        OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClientMatchAndAssert(
                        Tuples.of(
                                arg -> arg.contains("Generate a short funny"),
                                "A-RESULT",
                                arg -> {}),
                        Tuples.of(
                                arg -> arg.contains("plan"),
                                "{\"plan\":{\n"
                                    + "\"rationale\": \"the list contains a function that can turn"
                                    + " a scenario into a short and entertaining poem\",\n"
                                    + "\"function\": \"WriterSkill.ShortPoem\",\n"
                                    + "\"parameters\": {\n"
                                    + "\"input\": \"Cleopatra\"\n"
                                    + "}}}",
                                request -> {
                                    Assertions.assertTrue(
                                            request.contains("WriterSkill.NovelOutline"));
                                    Assertions.assertTrue(
                                            request.contains("WriterSkill.Brainstorm"));
                                    Assertions.assertTrue(request.contains("WriterSkill.Acronym"));
                                    Assertions.assertTrue(
                                            request.contains("WriterSkill.ShortPoem"));
                                    Assertions.assertTrue(request.contains("WriterSkill.EmailTo"));
                                    Assertions.assertTrue(request.contains("WriterSkill.EmailGen"));
                                    Assertions.assertTrue(request.contains("WriterSkill.Rewrite"));
                                    Assertions.assertTrue(
                                            request.contains("WriterSkill.Translate"));

                                    Assertions.assertTrue(
                                            request.contains("SummarizeSkill.Topics"));
                                    Assertions.assertTrue(
                                            request.contains(
                                                    "SummarizeSkill.MakeAbstractReadable"));
                                    Assertions.assertTrue(
                                            request.contains("SummarizeSkill.Notegen"));
                                    Assertions.assertTrue(
                                            request.contains("SummarizeSkill.Summarize"));
                                    Assertions.assertTrue(
                                            request.contains("SummarizeSkill.Topics"));
                                }));

        ActionPlanner planner = createPlanner(client);
        String goal = "Write a poem about Cleopatra.";
        Plan plan = planner.createPlanAsync(goal).block();
        String planResult = plan.invokeAsync(goal).block().getResult();
        Assertions.assertEquals("A-RESULT", planResult);
    }

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

    public static ActionPlanner createPlanner(OpenAIAsyncClient client) {
        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.textCompletionService()
                                        .build(client, "text-davinci-002"))
                        .build();

        kernel.importSkillFromDirectory("SummarizeSkill", "../../samples/skills", "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", "../../samples/skills", "WriterSkill");

        // Create an instance of ActionPlanner.
        // The ActionPlanner takes one goal and returns a single function to execute.
        ActionPlanner planner = new ActionPlanner(kernel, null);
        return planner;
    }
}
