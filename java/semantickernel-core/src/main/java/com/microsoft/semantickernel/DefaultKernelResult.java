package com.microsoft.semantickernel;

import com.microsoft.semantickernel.KernelResult;
import com.microsoft.semantickernel.orchestration.FunctionResult;

import java.util.Collection;

public class DefaultKernelResult implements KernelResult {
    private Collection<FunctionResult> results;

    public DefaultKernelResult(Collection<FunctionResult> results) {
        this.results = results;
    }

    @Override
    public Collection<FunctionResult> functionResults() {
        return this.results;
    }
}
