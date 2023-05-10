// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.textcompletion.CompletionSkFunction;

/** Provides various builders for completion functions */
public interface FunctionBuilders {

    static SequentialPlannerSKFunction.Builder getPlannerBuilder() {
        return BuildersSingleton.INST.getFunctionBuilders().plannerBuilders();
    }

    static CompletionSkFunction.Builder getCompletionBuilder() {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders();
    }

    CompletionSkFunction.Builder completionBuilders();

    SequentialPlannerSKFunction.Builder plannerBuilders();
}
