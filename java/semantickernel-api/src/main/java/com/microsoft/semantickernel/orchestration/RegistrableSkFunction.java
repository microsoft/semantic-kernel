// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;

public interface RegistrableSkFunction {

    void registerOnKernel(Kernel kernel);
}
