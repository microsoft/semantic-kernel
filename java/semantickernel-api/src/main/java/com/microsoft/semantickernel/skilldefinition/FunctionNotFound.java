// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

public class FunctionNotFound extends RuntimeException {
    public FunctionNotFound(String functionName) {
        super("Could not find function: " + functionName);
    }
}
