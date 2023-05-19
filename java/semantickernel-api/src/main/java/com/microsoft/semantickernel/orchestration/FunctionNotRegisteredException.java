// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

public class FunctionNotRegisteredException extends RuntimeException {

    public FunctionNotRegisteredException(String name) {
        super(
                "It does not appear this function("
                        + name
                        + ") has been registered on a kernel.\n"
                        + "Register it on a kernel either by passing it to"
                        + " KernelConfig.Builder().addSkill() when building the kernel, or\n"
                        + "passing it to Kernel.registerSemanticFunction");
    }
}
