// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import java.util.Collection;

/**
 * @since 1.0.0
 */
public interface KernelResult {

    /**
     * Get the results from all functions in pipeline.
     *
     * @return The results from all functions in pipeline.
     */
    Collection<FunctionResult> functionResults();
}
