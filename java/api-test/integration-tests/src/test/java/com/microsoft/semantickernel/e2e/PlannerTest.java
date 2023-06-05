// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class PlannerTest extends AbstractKernelTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(PlannerTest.class);

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void executeInlineFunction() throws IOException {
        Kernel kernel = buildTextCompletionKernel();
        kernel.importSkill(
                "SummarizeSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../../samples/skills", "SummarizeSkill"));
        kernel.importSkill(
                "WriterSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../../samples/skills", "WriterSkill"));

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

        CompletionSKContext result =
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian.")
                        .block();
        LOGGER.info("Result: " + result.getResult());
    }
}
