// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.planner.SequentialPlannerSKFunction;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

/** Provides various builders for completion functions */
public interface FunctionBuilders {

    static SequentialPlannerSKFunction.Builder getPlannerBuilder() {
        return BuildersSingleton.INST.getFunctionBuilders().plannerBuilders();
    }

    static CompletionSKFunction.Builder getCompletionBuilder() {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders();
    }

    CompletionSKFunction.Builder completionBuilders();

    SequentialPlannerSKFunction.Builder plannerBuilders();
}
