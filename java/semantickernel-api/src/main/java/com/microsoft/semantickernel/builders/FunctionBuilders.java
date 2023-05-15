// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import javax.annotation.Nullable;

/** Provides various builders for completion functions */
public interface FunctionBuilders {

    static SequentialPlannerSKFunction.Builder getPlannerBuilder() {
        return getPlannerBuilder(null);
    }

    static SequentialPlannerSKFunction.Builder getPlannerBuilder(@Nullable Kernel kernel) {
        return BuildersSingleton.INST.getFunctionBuilders().plannerBuilders(kernel);
    }

    static CompletionSKFunction.Builder getCompletionBuilder() {
        return getCompletionBuilder(null);
    }

    static CompletionSKFunction.Builder getCompletionBuilder(@Nullable Kernel kernel) {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders(kernel);
    }

    CompletionSKFunction.Builder completionBuilders(@Nullable Kernel kernel);

    SequentialPlannerSKFunction.Builder plannerBuilders(@Nullable Kernel kernel);
}
