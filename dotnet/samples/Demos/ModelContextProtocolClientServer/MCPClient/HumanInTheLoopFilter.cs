// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// A filter that intercepts function invocations to allow for human-in-the-loop processing.
/// </summary>
public class HumanInTheLoopFilter : IFunctionInvocationFilter
{
    /// <inheritdoc />
    public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        // Intercept the MCP sampling handler before invoking it
        if (context.Function.Name == "MCPSamplingHandler")
        {
            CreateMessageRequestParams request = (CreateMessageRequestParams)context.Arguments["request"]!;

            if (!GetUserApprovalForSamplingMessages(request))
            {
                context.Result = new FunctionResult(context.Result, "Operation was rejected due to PII.");
                return Task.CompletedTask;
            }
        }

        // Proceed with the handler invocation
        return next.Invoke(context);
    }

    /// <summary>
    /// Checks if the user approves the messages for further sampling request processing.
    /// </summary>
    /// <remarks>
    /// This method serves as a placeholder for the actual implementation, which may involve user interaction through a user interface.
    /// The user will be presented with a list of messages and given two options: to approve or reject the request.
    /// </remarks>
    /// <param name="request">The sampling request.</param>
    /// <returns>Returns true if the user approves; otherwise, false.</returns>
    private static bool GetUserApprovalForSamplingMessages(CreateMessageRequestParams request)
    {
        // Approve the request
        return true;
    }
}
