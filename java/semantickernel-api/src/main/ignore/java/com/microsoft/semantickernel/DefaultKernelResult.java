// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;

public class DefaultKernelResult implements KernelResult {

    private Collection<FunctionResult> results;

    public DefaultKernelResult(Collection<FunctionResult> results) {
        this.results = new ArrayList<>(results);
    }

    @Override
    public Collection<FunctionResult> functionResults() {
        return Collections.unmodifiableCollection(this.results);
    }
}
