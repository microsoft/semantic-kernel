// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.HashSet;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.util.function.Tuples;

public class SequentialPlannerTest {

    public static class SkillWithSomeArgs {

        @DefineSKFunction(name = "aFunction")
        public String aFunction(
                @SKFunctionParameters(
                                name = "input1",
                                description = "The first input to the function")
                        String input1,
                @SKFunctionParameters(
                                name = "input2",
                                description = "The second input to the function")
                        String input2) {
            return "A-RESULT";
        }
    }

    @Test
    public void inputsAreCorrectlyPassed() {
        String planXml =
                "<plan>\n"
                        + "    <function.SkillWithSomeArgs.aFunction input1=\"Cleopatra\""
                        + " input2=\"Anthony\" />\n"
                        + "    </plan>";
        Kernel kernel = mockKernelWithPlan(planXml);

        SkillWithSomeArgs skill = Mockito.spy(new SkillWithSomeArgs());
        kernel.importSkill(skill, "SkillWithSomeArgs");

        SequentialPlanner planner =
                new SequentialPlanner(kernel, new SequentialPlannerRequestSettings(), null);

        String goal = "Write a poem about Cleopatra.";

        Plan plan = planner.createPlanAsync(goal).block();
        String planResult = plan.invokeAsync(goal).block().getResult();

        Assertions.assertEquals("A-RESULT", planResult);

        Mockito.verify(skill, Mockito.atLeastOnce()).aFunction("Cleopatra", "Anthony");
    }

    @Test
    public void givenDefaultSettings_WhenPlanWithMissingFunctionsIsGenerated_ShouldThrow() {
        String planXml =
                "<plan>\n"
                        + "    <function.SkillWithSomeArgs.aFunction input1=\"Cleopatra\""
                        + " input2=\"Anthony\" />\n"
                        + "    </plan>";
        Kernel kernel = mockKernelWithPlan(planXml); // don't load any skills & functions

        SequentialPlanner planner =
                new SequentialPlanner(kernel, new SequentialPlannerRequestSettings(), null);

        String goal = "Write a poem about Cleopatra.";

        Assertions.assertThrows(PlanningException.class, planner.createPlanAsync(goal)::block);
    }

    @Test
    public void
            givenAllowMissingFunctionsSetting_WhenPlanWithMissingFunctionsIsGenerated_ShouldNotThrow() {
        String planXml =
                "<plan>\n"
                        + "    <function.SkillWithSomeArgs.aFunction input1=\"Cleopatra\""
                        + " input2=\"Anthony\" />\n"
                        + "    </plan>";
        Kernel kernel = mockKernelWithPlan(planXml); // don't load any skills & functions

        SequentialPlannerRequestSettings settings =
                new SequentialPlannerRequestSettings(
                        null, 10, new HashSet<>(), new HashSet<>(), new HashSet<>(), 1024, true);
        SequentialPlanner planner = new SequentialPlanner(kernel, settings, null);

        String goal = "Write a poem about Cleopatra.";

        Plan plan = planner.createPlanAsync(goal).block();
        String planResult = plan.invokeAsync(goal).block().getResult();
    }

    private static Kernel mockKernelWithPlan(String planXml) {
        OpenAIAsyncClient client = mockCompletionOpenAIAsyncClient(Tuples.of("plan", planXml));

        TextCompletion textCompletion =
                SKBuilders.textCompletion()
                        .withModelId("text-davinci-002")
                        .withOpenAIClient(client)
                        .build();

        return SKBuilders.kernel().withDefaultAIService(textCompletion).build();
    }
}
