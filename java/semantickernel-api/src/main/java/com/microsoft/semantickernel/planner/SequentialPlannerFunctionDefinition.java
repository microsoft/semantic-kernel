// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SemanticFunctionDefinition;

import java.util.function.Function;

public abstract class SequentialPlannerFunctionDefinition
        extends SemanticFunctionDefinition<
                Void, SequentialPlannerSKContext, SequentialPlannerSKFunction> {
    public static SequentialPlannerFunctionDefinition of(
            Function<Kernel, SequentialPlannerSKFunction> func) {
        return new SequentialPlannerFunctionDefinition() {
            @Override
            protected SequentialPlannerSKFunction build(Kernel kernel) {
                return func.apply(kernel);
            }
        };
    }
}
