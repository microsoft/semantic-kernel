// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.actionplanner;

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.util.function.Tuples;

public class ActionPlannerTest {

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
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of(
                                "plan",
                                "{\n"
                                        + "   \"plan\" : {\n"
                                        + "      \"function\" : \"SkillWithSomeArgs.aFunction\",\n"
                                        + "      \"parameters\" : {\n"
                                        + "         \"input1\" : \"Cleopatra\",\n"
                                        + "         \"input2\" : \"Anthony\"\n"
                                        + "      },\n"
                                        + "      \"rationale\" : \"na\"\n"
                                        + "   }\n"
                                        + "}\n"));

        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.textCompletionService()
                                        .build(client, "text-davinci-002"))
                        .build();

        SkillWithSomeArgs skill = Mockito.spy(new SkillWithSomeArgs());
        kernel.importSkill(skill, "SkillWithSomeArgs");

        ActionPlanner planner = new ActionPlanner(kernel, null);

        String goal = "Write a poem about Cleopatra.";

        Plan plan = planner.createPlanAsync(goal).block();
        String planResult = plan.invokeAsync(goal).block().getResult();

        Assertions.assertEquals("A-RESULT", planResult);

        Mockito.verify(skill, Mockito.atLeastOnce()).aFunction("Cleopatra", "Anthony");
    }
}
