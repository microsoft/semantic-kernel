// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.functions;

public class SemanticFunctionResult {

    private String result;

    public SemanticFunctionResult() {}

    public SemanticFunctionResult(String result) {
        this.result = result;
    }

    public String getResult() {
        return this.result;
    }
}
