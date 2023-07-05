// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKException;

public class FunctionNotRegisteredException extends SKException {

    public FunctionNotRegisteredException(String name) {
        super(
                String.format(
                        "It does not appear this function(%s) has been registered on a kernel.%n"
                                + "Register it on a kernel either by passing it to "
                                + "KernelConfig.Builder().addSkill() when building the kernel, or%n"
                                + "passing it to Kernel.registerSemanticFunction",
                        name));
    }
}
