// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;

// Currently the kernel config does not have and function within Java
public final class KernelConfig implements Buildable {

    public static Builder builder() {
        return BuildersSingleton.INST.getInstance(KernelConfig.Builder.class);
    }

    public static class Builder implements SemanticKernelBuilder<KernelConfig> {
        public KernelConfig build() {
            return new KernelConfig();
        }
    }
}
