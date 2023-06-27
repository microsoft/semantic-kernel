// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

/** Provides various builders for completion functions */
public interface FunctionBuilders {

    static CompletionSKFunction.Builder getCompletionBuilder(Kernel kernel) {
        return BuildersSingleton.INST.getFunctionBuilders().completionBuilders(kernel);
    }

    CompletionSKFunction.Builder completionBuilders(Kernel kernel);
}
