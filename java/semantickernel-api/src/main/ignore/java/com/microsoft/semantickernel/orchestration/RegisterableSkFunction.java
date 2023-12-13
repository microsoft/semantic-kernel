// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;

public interface RegisterableSkFunction {

    void registerOnKernel(Kernel kernel);
}
