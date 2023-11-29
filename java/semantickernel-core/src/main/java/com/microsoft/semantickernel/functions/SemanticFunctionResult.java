package com.microsoft.semantickernel.functions;

public class SemanticFunctionResult {

    private String result;

    public FunctionResult() {
    }

    public FunctionResult(String result) {
        this.result = result;
    }

    public String getResult () {
        return this.result;
    }
}
