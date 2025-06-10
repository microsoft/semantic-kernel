// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.Extensions.AI;

/// <summary>
/// Specialization of <see cref="FunctionInvokingChatClient"/> that uses <see cref="KernelFunction"/> and supports <see cref="IAutoFunctionInvocationFilter"/>.
/// </summary>
internal sealed class KernelFunctionInvokingChatClient : FunctionInvokingChatClient
{
    /// <inheritdoc/>
    public KernelFunctionInvokingChatClient(IChatClient innerClient, ILoggerFactory? loggerFactory = null, IServiceProvider? functionInvocationServices = null)
        : base(innerClient, loggerFactory, functionInvocationServices)
    {
        this.MaximumIterationsPerRequest = 128;
    }

    /// <summary>
    /// Invokes the auto function invocation filters.
    /// </summary>
    /// <param name="context">The auto function invocation context.</param>
    /// <param name="functionCallCallback">The function to call after the filters.</param>
    /// <returns>The auto function invocation context.</returns>
    private async Task<AutoFunctionInvocationContext> OnAutoFunctionInvocationAsync(
        AutoFunctionInvocationContext context,
        Func<AutoFunctionInvocationContext, Task> functionCallCallback)
    {
        await this.InvokeFilterOrFunctionAsync(functionCallCallback, context).ConfigureAwait(false);

        return context;
    }

    /// <summary>
    /// This method will execute auto function invocation filters and function recursively.
    /// If there are no registered filters, just function will be executed.
    /// If there are registered filters, filter on <paramref name="index"/> position will be executed.
    /// Second parameter of filter is callback. It can be either filter on <paramref name="index"/> + 1 position or function if there are no remaining filters to execute.
    /// Function will always be executed as last step after all filters.
    /// </summary>
    private async Task InvokeFilterOrFunctionAsync(
        Func<AutoFunctionInvocationContext, Task> functionCallCallback,
        AutoFunctionInvocationContext context,
        int index = 0)
    {
        IList<IAutoFunctionInvocationFilter> autoFunctionInvocationFilters = context.Kernel.AutoFunctionInvocationFilters;

        if (autoFunctionInvocationFilters is { Count: > 0 } && index < autoFunctionInvocationFilters.Count)
        {
            await autoFunctionInvocationFilters[index].OnAutoFunctionInvocationAsync(
                context,
                (ctx) => this.InvokeFilterOrFunctionAsync(functionCallCallback, ctx, index + 1)
            ).ConfigureAwait(false);
        }
        else
        {
            await functionCallCallback(context).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    protected override async ValueTask<object?> InvokeFunctionAsync(Microsoft.Extensions.AI.FunctionInvocationContext context, CancellationToken cancellationToken)
    {
        if (context.Options is null || context.Options is not KernelChatOptions kernelChatOptions)
        {
            return await context.Function.InvokeAsync(context.Arguments, cancellationToken).ConfigureAwait(false);
        }

        object? result = null;

        kernelChatOptions.ChatMessageContent = context.Messages.Last().ToChatMessageContent();

        var autoContext = new AutoFunctionInvocationContext(kernelChatOptions, context.Function)
        {
            AIFunction = context.Function,
            Arguments = new KernelArguments(context.Arguments) { Services = this.FunctionInvocationServices },
            Messages = context.Messages,
            CallContent = context.CallContent,
            Iteration = context.Iteration,
            FunctionCallIndex = context.FunctionCallIndex,
            FunctionCount = context.FunctionCount,
            IsStreaming = context.IsStreaming
        };

        autoContext = await this.OnAutoFunctionInvocationAsync(
            autoContext,
            async (ctx) =>
            {
                // Check if filter requested termination
                if (ctx.Terminate)
                {
                    return;
                }

                // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                ctx.Result = await autoContext.Function.InvokeAsync(kernelChatOptions.Kernel, autoContext.Arguments, cancellationToken).ConfigureAwait(false);
            }).ConfigureAwait(false);
        result = autoContext.Result.GetValue<object>();

        context.Terminate = autoContext.Terminate;

        return result;
    }

    public override Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        // If the autoInvoke is false, we don't call any function, just process the messages as is.
        if (options is KernelChatOptions kernelChatOptions && (
                kernelChatOptions.ExecutionSettings?.FunctionChoiceBehavior is AutoFunctionChoiceBehavior autoFunctionChoiceBehavior && !autoFunctionChoiceBehavior.AutoInvoke
                || kernelChatOptions.ExecutionSettings?.FunctionChoiceBehavior is RequiredFunctionChoiceBehavior requiredFunctionChoiceBehavior && !requiredFunctionChoiceBehavior.AutoInvoke
            ))
        {
            // Skip function invocation
            return base.InnerClient.GetResponseAsync(messages, options, cancellationToken);
        }

        return base.GetResponseAsync(messages, options, cancellationToken);
    }

    public override IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        // If the autoInvoke is false, we don't call any function, just process the messages as is.
        if (options is KernelChatOptions kernelChatOptions && (
                kernelChatOptions.ExecutionSettings?.FunctionChoiceBehavior is AutoFunctionChoiceBehavior autoFunctionChoiceBehavior && !autoFunctionChoiceBehavior.AutoInvoke
                || kernelChatOptions.ExecutionSettings?.FunctionChoiceBehavior is RequiredFunctionChoiceBehavior requiredFunctionChoiceBehavior && !requiredFunctionChoiceBehavior.AutoInvoke
            ))
        {
            // Skip function invocation
            return base.InnerClient.GetStreamingResponseAsync(messages, options, cancellationToken);
        }

        return base.GetStreamingResponseAsync(messages, options, cancellationToken);
    }
}
