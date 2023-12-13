package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.KernelFunction;

public abstract class DefaultKernelFunction implements KernelFunction {

    @Override
    public String getSkillName() {
        return null;
    }

    @Override
    public String getName() {
        return null;
    }

    @Override
    public String toFullyQualifiedName() {
        return null;
    }

    @Override
    public String getDescription() {
        return null;
    }

    @Override
    public String toEmbeddingString() {
        return null;
    }

    @Override
    public String toManualString(boolean includeOutputs) {
        return null;
    }
}
