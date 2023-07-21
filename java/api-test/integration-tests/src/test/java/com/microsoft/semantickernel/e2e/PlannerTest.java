// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PlannerTest extends AbstractKernelTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(PlannerTest.class);

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void executeInlineFunction() throws ConfigurationException {
        Kernel kernel = buildTextCompletionKernel();
        kernel.importSkillFromDirectory(
                "SummarizeSkill", "../../../samples/skills", "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", "../../../samples/skills", "WriterSkill");

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

        Plan plan =
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian.")
                        .block();

        SKContext result = plan.invokeAsync().block();

        LOGGER.info("Result: " + result.getResult());
    }
}
