package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.BuildersSingleton;

public interface KernelArguments extends
    com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments {
    
    static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

}
