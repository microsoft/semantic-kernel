///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.extensions:semantickernel-sequentialplanner-extension:0.2.6-alpha
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java,Example00_GettingStarted.java
package com.microsoft.semantickernel.samples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.samples.syntaxexamples.SampleSkillsUtil;

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
