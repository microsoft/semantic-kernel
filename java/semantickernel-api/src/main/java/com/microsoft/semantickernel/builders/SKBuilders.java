// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.orchestration.ReadOnlyContextVariables;
import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class SKBuilders {

    public static CompletionSKFunction.Builder completionFunctions() {
        return FunctionBuilders.getCompletionBuilder();
    }

    public static SequentialPlannerSKFunction.Builder plannerFunctions() {
        return FunctionBuilders.getPlannerBuilder();
    }

    public static TextCompletion.Builder textCompletionService() {
        return BuildersSingleton.INST.getTextCompletionBuilder();
    }

    public static Kernel.Builder kernel() {
        return new Kernel.Builder();
    }

    public static KernelConfig.Builder kernelConfig() {
        return new KernelConfig.Builder();
    }

    public static ReadOnlySkillCollection.Builder skillCollection() {
        return BuildersSingleton.INST.getReadOnlySkillCollection();
    }

    public static PromptTemplate.Builder promptTemplate() {
        return BuildersSingleton.INST.getPromptTemplateBuilder();
    }

    public static ReadOnlyContextVariables.Builder variables() {
        return BuildersSingleton.INST.variables();
    }
}
