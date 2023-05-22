// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.SKException;

public class FunctionNotFound extends SKException {
    public FunctionNotFound(String functionName) {
        super("Could not find function: " + functionName);
    }
}
