// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

/*

TODO: integrate planner
public class PlannerTest extends AbstractKernelTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(PlannerTest.class);

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void executeInlineFunction() throws IOException {
        Kernel kernel = buildTextCompletionKernel();
        kernel.importSkills(
                "SummarizeSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../../samples/skills", "SummarizeSkill"));
        kernel.importSkills(
                "WriterSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../../samples/skills", "WriterSkill"));

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

        SequentialPlannerSKContext result =
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian.")
                        .block();
        LOGGER.info("Result: " + result.getResult());
    }
}
*/