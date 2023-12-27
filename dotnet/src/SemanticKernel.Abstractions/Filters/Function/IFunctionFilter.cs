// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public interface IFunctionFilter
{
    void OnFunctionInvoking(FunctionInvokingContext context);

    void OnFunctionInvoked(FunctionInvokedContext context);
}
