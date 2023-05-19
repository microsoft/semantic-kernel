// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.planner.SequentialPlannerSKContext;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;

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
        kernel.importSkills(
                "SummarizeSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../samples/skills", "SummarizeSkill"));
        kernel.importSkills(
                "WriterSkill",
                KernelExtensions.importSemanticSkillFromDirectory(
                        "../../samples/skills", "WriterSkill"));

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

        SequentialPlannerSKContext result =
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian.")
                        .block();
        LOGGER.info("Result: " + result.getResult());
        /*

        {
            Console.WriteLine("======== Planning - Create and Execute Poetry Plan ========");
            var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
            kernel.Config.AddAzureTextCompletionService(
                Env.Var("AZURE_OPENAI_SERVICE_ID"),
                Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_ENDPOINT"),
                Env.Var("AZURE_OPENAI_KEY"));

            string folder = RepoFiles.SampleSkillsPath();
            kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");
            kernel.ImportSemanticSkillFromDirectory(folder, "WriterSkill");

            var planner = new SequentialPlanner(kernel);

            var planObject = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");

            Console.WriteLine("Original plan:");
            Console.WriteLine(planObject.ToJson());

            var result = await kernel.RunAsync(planObject);

            Console.WriteLine("Result:");
            Console.WriteLine(result.Result);

             */
    }
}
