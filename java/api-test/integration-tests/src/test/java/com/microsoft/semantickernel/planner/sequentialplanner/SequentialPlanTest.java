// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class SequentialPlanTest {

    public static class Skills {
        @DefineSKFunction(name = "Skill1")
        public String skill1(@SKFunctionInputAttribute(description = "an input") String input) {
            return input + "::Skill1";
        }

        @DefineSKFunction(name = "Skill2")
        public String skill2(@SKFunctionInputAttribute(description = "an input") String input) {
            return input + "::Skill2";
        }

        @DefineSKFunction(name = "Skill3")
        public String skill3(
                @SKFunctionInputAttribute(description = "an input") String input,
                @SKFunctionParameters(
                                description = "a variable to set the result to",
                                required = true,
                                name = "secondInput")
                        String secondInput) {
            return input + "::" + secondInput + "::Skill3";
        }

        @DefineSKFunction(name = "Skill4")
        public String skill4(
                @SKFunctionParameters(
                                description = "a variable to set the result to",
                                required = true,
                                name = "anarg")
                        String anarg) {
            return anarg + "::Skill4";
        }
    }

    @Test
    public void withDirectInput() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1 input="John Doe"/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("John Doe::Skill1", result.getResult());
    }

    @Test
    public void withNoInput() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill1", result.getResult());
    }

    @Test
    public void withChainedInput() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1/>
                          <function.Skills.Skill2/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill1::Skill2", result.getResult());
    }

    @Test
    public void settingAVariable() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1 setContextVariable="A"/>
                          <function.Skills.Skill2/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill2", result.getResult());
        Assertions.assertEquals("Foo::Skill1", result.getVariables().get("A"));
    }

    @Test
    public void usingAVariable() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1 setContextVariable="A"/>
                          <function.Skills.Skill2 input="$A"/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill1::Skill2", result.getResult());
        Assertions.assertEquals("Foo::Skill1", result.getVariables().get("A"));
    }

    @Test
    public void withASecondArg() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1 setContextVariable="A"/>
                          <function.Skills.Skill2 input="$A"/>
                          <function.Skills.Skill3 secondInput="x"/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill1::Skill2::x::Skill3", result.getResult());
        Assertions.assertEquals("Foo::Skill1", result.getVariables().get("A"));
    }

    @Test
    public void noInput() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill1 setContextVariable="A"/>
                          <function.Skills.Skill2 input="$A"/>
                          <function.Skills.Skill3 secondInput="x"/>
                          <function.Skills.Skill4 anarg="$A"/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("Foo::Skill1::Skill4", result.getResult());
        Assertions.assertEquals("Foo::Skill1", result.getVariables().get("A"));
    }

    @Test
    public void noInput2() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill4 anarg="foo"/>
                        </plan><!-- END -->
                        """;

        SKContext result = makePlan(planString).invokeAsync("Foo").block();
        Assertions.assertEquals("foo::Skill4", result.getResult());
    }

    @Test
    public void noInput3() {
        String planString =
                """
                        <plan>
                          <function.Skills.Skill4/>
                        </plan><!-- END -->
                        """;
        SKContext context = SKBuilders.context().build().setVariable("anarg", "foo");
        SKContext result = makePlan(planString).invokeAsync(context).block();
        Assertions.assertEquals("foo::Skill4", result.getResult());
    }

    private static Plan makePlan(String planString) {
        Kernel kernel =
                SKBuilders.kernel().withKernelConfig(SKBuilders.kernelConfig().build()).build();
        kernel.importSkill(new Skills(), "Skills");

        return SequentialPlanParser.toPlanFromXml(planString.stripIndent(), "", kernel.getSkills());
    }
}
