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

    private static void UpdateOptionsForAutoFunctionInvocation(ref ChatOptions options, ChatMessageContent content, bool isStreaming)
    {
        if (options.AdditionalProperties?.ContainsKey(ChatOptionsExtensions.IsStreamingKey) ?? false)
        {
            throw new KernelException($"The reserved key name '{ChatOptionsExtensions.IsStreamingKey}' is already specified in the options. Avoid using this key name.");
        }

        if (options.AdditionalProperties?.ContainsKey(ChatOptionsExtensions.ChatMessageContentKey) ?? false)
        {
            throw new KernelException($"The reserved key name '{ChatOptionsExtensions.ChatMessageContentKey}' is already specified in the options. Avoid using this key name.");
        }

        options.AdditionalProperties ??= [];

        options.AdditionalProperties[ChatOptionsExtensions.IsStreamingKey] = isStreaming;
        options.AdditionalProperties[ChatOptionsExtensions.ChatMessageContentKey] = content;
    }

    private static void ClearOptionsForAutoFunctionInvocation(ref ChatOptions options)
    {
        if (options.AdditionalProperties?.ContainsKey(ChatOptionsExtensions.IsStreamingKey) ?? false)
        {
            options.AdditionalProperties.Remove(ChatOptionsExtensions.IsStreamingKey);
        }

        if (options.AdditionalProperties?.ContainsKey(ChatOptionsExtensions.ChatMessageContentKey) ?? false)
        {
            options.AdditionalProperties.Remove(ChatOptionsExtensions.ChatMessageContentKey);
        }
    }

    /// <inheritdoc/>
    protected override async Task<(bool ShouldTerminate, int NewConsecutiveErrorCount, IList<ChatMessage> MessagesAdded)> ProcessFunctionCallsAsync(
        ChatResponse response, IList<ChatMessage> messages, ChatOptions options, IList<FunctionCallContent> functionCallContents, int iteration, int consecutiveErrorCount, bool isStreaming, CancellationToken cancellationToken)
    {
        // Prepare the options for the next auto function invocation iteration.
        UpdateOptionsForAutoFunctionInvocation(ref options!, response.Messages.Last().ToChatMessageContent(), isStreaming: false);

        // We must add a response for every tool call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
        var result = await base.ProcessFunctionCallsAsync(response, messages, options, functionCallContents, iteration, consecutiveErrorCount, isStreaming, cancellationToken).ConfigureAwait(false);

        // Clear the auto function invocation options.
        ClearOptionsForAutoFunctionInvocation(ref options);

        return result;
    }

    /// <inheritdoc/>
    protected override async Task<FunctionInvocationResult> ProcessFunctionCallAsync(
        IList<ChatMessage> messages, ChatOptions options, IList<FunctionCallContent> callContents,
        int iteration, int functionCallIndex, bool captureExceptions, bool isStreaming, CancellationToken cancellationToken)
    {
        var callContent = callContents[functionCallIndex];

        // Look up the AIFunction for the function call. If the requested function isn't available, send back an error.
        AIFunction? function = options.Tools!.OfType<AIFunction>().FirstOrDefault(t => t.Name == callContent.Name);
        if (function is null)
        {
            return new(shouldTerminate: false, FunctionInvocationStatus.NotFound, callContent, result: null, exception: null);
        }

        var context = new AutoFunctionInvocationContext(options)
        {
            AIFunction = function,
            Arguments = new KernelArguments(callContent.Arguments ?? new Dictionary<string, object?>()) { Services = this.FunctionInvocationServices },
            Messages = messages,
            CallContent = callContent,
            Iteration = iteration,
            FunctionCallIndex = functionCallIndex,
            FunctionCount = callContents.Count,
            IsStreaming = isStreaming
        };

        object? result;
        try
        {
            result = await base.InvokeFunctionAsync(context, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e) when (!cancellationToken.IsCancellationRequested)
        {
            if (!captureExceptions)
            {
                throw;
            }

            return new(
                shouldTerminate: false,
                FunctionInvocationStatus.Exception,
                callContent,
                result: null,
                exception: e);
        }

        return new(
            shouldTerminate: context.Terminate,
            FunctionInvocationStatus.RanToCompletion,
            callContent,
            result,
            exception: null);
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
    protected override async Task<(FunctionInvocationContext context, object? result)> InvokeFunctionCoreAsync(Microsoft.Extensions.AI.FunctionInvocationContext context, CancellationToken cancellationToken)
    {
        object? result = null;
        if (context is AutoFunctionInvocationContext autoContext)
        {
            context = await this.OnAutoFunctionInvocationAsync(
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
                    result = await autoContext.AIFunction.InvokeAsync(new(context.Arguments), cancellationToken).ConfigureAwait(false);
                    ctx.Result = new FunctionResult(ctx.Function, result);
                }).ConfigureAwait(false);
            result = autoContext.Result.GetValue<object>();
        }
        else
        {
            result = await context.Function.InvokeAsync(new(context.Arguments), cancellationToken).ConfigureAwait(false);
        }

        return (context, result);
    }
}
