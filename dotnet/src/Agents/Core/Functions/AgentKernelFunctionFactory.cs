// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides factory methods for creating implementations of <see cref="KernelFunction"/> backed by an <see cref="Agent" />.
/// </summary>
[Experimental("SKEXP0110")]
public static class AgentKernelFunctionFactory
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> that will invoke the provided Agent.
    /// </summary>
    /// <param name="agent">The <see cref="Agent" /> to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to the agent name.</param>
    /// <param name="description">The description to use for the function. If null, it will default to agent description.</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to query and additional instructions parameters.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the <see cref="Agent"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFromAgent(
        Agent agent,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(agent);

        async Task<FunctionResult> InvokeAgentAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            var queryString = query?.ToString() ?? string.Empty;

            AgentInvokeOptions? options = null;

            if (arguments.TryGetValue("instructions", out var instructions) && instructions is not null)
            {
                options = new()
                {
                    AdditionalInstructions = instructions?.ToString() ?? string.Empty
                };
            }

            var response = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, queryString), null, options, cancellationToken);
            var responseItems = await response.ToArrayAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
            var chatMessages = responseItems.Select(i => i.Message).ToArray();
            return new FunctionResult(function, chatMessages, kernel.Culture);
        }

        KernelFunctionFromMethodOptions options = new()
        {
            FunctionName = functionName ?? agent.GetName(),
            Description = description ?? agent.Description,
            Parameters = parameters ?? GetDefaultKernelParameterMetadata(),
            ReturnParameter = new() { ParameterType = typeof(FunctionResult) },
        };

        return KernelFunctionFactory.CreateFromMethod(
                InvokeAgentAsync,
                options);
    }

    #region private
    [RequiresUnreferencedCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    private static IEnumerable<KernelParameterMetadata> GetDefaultKernelParameterMetadata()
    {
        return s_kernelParameterMetadata ??= [
            new KernelParameterMetadata("query") { Description = "Available information that will guide in performing this operation.", ParameterType = typeof(string), IsRequired = true },
            new KernelParameterMetadata("instructions") { Description = "Additional instructions for the agent.", ParameterType = typeof(string), IsRequired = true },
        ];
    }

    private static IEnumerable<KernelParameterMetadata>? s_kernelParameterMetadata;
    #endregion
}
