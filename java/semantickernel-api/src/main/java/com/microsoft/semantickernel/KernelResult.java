package com.microsoft.semantickernel;

import java.util.Collection;

import com.microsoft.semantickernel.orchestration.FunctionResult;

/**
 * @since 1.0.0
 */
public interface KernelResult {

    /**
     * Get the results from all functions in pipeline.
     * @return The results from all functions in pipeline.
     */
    Collection<FunctionResult> functionResults();

}
