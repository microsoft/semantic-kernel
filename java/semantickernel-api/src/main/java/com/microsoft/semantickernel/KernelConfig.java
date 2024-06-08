// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;

// Currently the kernel config does not have and function within Java
public final class KernelConfig implements Buildable {

    public static Builder builder() {
<<<<<<< HEAD
        return BuildersSingleton.INST.getInstance(KernelConfig.Builder.class);
=======
      return BuildersSingleton.INST.getInstance(KernelConfig.Builder.class);
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
    }

    public static class Builder implements SemanticKernelBuilder<KernelConfig> {
        public KernelConfig build() {
            return new KernelConfig();
        }
    }
}
