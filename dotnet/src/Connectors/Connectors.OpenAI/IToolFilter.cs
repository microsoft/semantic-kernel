// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

public interface IToolFilter
{
    /// <summary>
    /// Method which is executed before tool invocation.
    /// </summary>
    /// <param name="context">Data related to tool before invocation.</param>
    void OnToolInvoking(ToolInvokingContext context);

    /// <summary>
    /// Method which is executed after tool invocation.
    /// </summary>
    /// <param name="context">Data related to tool after invocation.</param>
    void OnToolInvoked(ToolInvokedContext context);
}
