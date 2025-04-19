// Copyright (c) Microsoft. All rights reserved.

using System;
#pragma warning restore IDE0073 // The file header does not match the required text
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

// Modified source from 2025-04-07
// https://raw.githubusercontent.com/dotnet/extensions/84d09b794d994435568adcbb85a981143d4f15cb/src/Libraries/Microsoft.Extensions.AI/ChatCompletion/FunctionInvokingChatClient.cs

namespace Microsoft.Extensions.AI;

/// <summary>
/// Specialization of <see cref="FunctionInvokingChatClientV2"/> that uses <see cref="KernelFunction"/> and supports <see cref="IAutoFunctionInvocationFilter"/>.
/// </summary>
internal sealed class KernelFunctionInvokingChatClient : FunctionInvokingChatClientV2
{
    /// <inheritdoc/>
    public KernelFunctionInvokingChatClient(IChatClient innerClient, ILoggerFactory? loggerFactory = null, IServiceProvider? functionInvocationServices = null)
        : base(innerClient, loggerFactory, functionInvocationServices)
    {
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
        ChatResponse response, List<ChatMessage> messages, ChatOptions options, List<FunctionCallContent> functionCallContents, int iteration, int consecutiveErrorCount, bool isStreaming, CancellationToken cancellationToken)
    {
        // Prepare the options for the next auto function invocation iteration.
        UpdateOptionsForAutoFunctionInvocation(ref options!, response.Messages.Last().ToChatMessageContent(), isStreaming: false);

        // We must add a response for every tool call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
        (bool ShouldTerminate, int NewConsecutiveErrorCount, IList<ChatMessage> MessagesAdded) result;
        Debug.Assert(functionCallContents.Count > 0, "Expected at least one function call.");
        var shouldTerminate = false;

        var captureCurrentIterationExceptions = consecutiveErrorCount < this.MaximumConsecutiveErrorsPerRequest;

        // Process all functions. If there's more than one and concurrent invocation is enabled, do so in parallel.
        if (functionCallContents.Count == 1)
        {
            FunctionInvocationResult functionResult = await this.ProcessFunctionCallAsync(
                messages, options, functionCallContents, iteration, 0, captureCurrentIterationExceptions, isStreaming, cancellationToken).ConfigureAwait(false);

            IList<ChatMessage> added = this.CreateResponseMessages([functionResult]);
            this.ThrowIfNoFunctionResultsAdded(added);
            this.UpdateConsecutiveErrorCountOrThrow(added, ref consecutiveErrorCount);

            messages.AddRange(added);
            result = (functionResult.ShouldTerminate, consecutiveErrorCount, added);
        }
        else
        {
            List<FunctionInvocationResult> results = [];

            var terminationRequested = false;
            if (this.AllowConcurrentInvocation)
            {
                // Rather than awaiting each function before invoking the next, invoke all of them
                // and then await all of them. We avoid forcibly introducing parallelism via Task.Run,
                // but if a function invocation completes asynchronously, its processing can overlap
                // with the processing of other the other invocation invocations.
                results.AddRange(await Task.WhenAll(
                    from i in Enumerable.Range(0, functionCallContents.Count)
                    select this.ProcessFunctionCallAsync(
                        messages, options, functionCallContents,
                        iteration, i, captureExceptions: true, isStreaming, cancellationToken)).ConfigureAwait(false));

                terminationRequested = results.Any(r => r.ShouldTerminate);
            }
            else
            {
                // Invoke each function serially.
                for (int i = 0; i < functionCallContents.Count; i++)
                {
                    var functionResult = await this.ProcessFunctionCallAsync(
                        messages, options, functionCallContents,
                        iteration, i, captureCurrentIterationExceptions, isStreaming, cancellationToken).ConfigureAwait(false);

                    results.Add(functionResult);

                    // Differently from the original FunctionInvokingChatClient, as soon the termination is requested,
                    // we stop and don't continue, if that can be parametrized, this override won't be needed
                    if (functionResult.ShouldTerminate)
                    {
                        shouldTerminate = true;
                        terminationRequested = true;
                        break;
                    }
                }
            }

            IList<ChatMessage> added = this.CreateResponseMessages(results);
            this.ThrowIfNoFunctionResultsAdded(added);
            this.UpdateConsecutiveErrorCountOrThrow(added, ref consecutiveErrorCount);

            messages.AddRange(added);

            if (!terminationRequested)
            {
                // If any function requested termination, we'll terminate.
                shouldTerminate = false;
                foreach (FunctionInvocationResult fir in results)
                {
                    shouldTerminate = shouldTerminate || fir.ShouldTerminate;
                }
            }

            result = (shouldTerminate, consecutiveErrorCount, added);
        }

        // Clear the auto function invocation options.
        ClearOptionsForAutoFunctionInvocation(ref options);

        return result;
    }

    /// <inheritdoc/>
    protected override async Task<FunctionInvocationResult> ProcessFunctionCallAsync(
        List<ChatMessage> messages, ChatOptions options, List<FunctionCallContent> callContents,
        int iteration, int functionCallIndex, bool captureExceptions, bool isStreaming, CancellationToken cancellationToken)
    {
        var callContent = callContents[functionCallIndex];

        // Look up the AIFunction for the function call. If the requested function isn't available, send back an error.
        AIFunction? function = options.Tools!.OfType<AIFunction>().FirstOrDefault(t => t.Name == callContent.Name);
        if (function is null)
        {
            return new(shouldTerminate: false, FunctionInvocationStatus.NotFound, callContent, result: null, exception: null);
        }

        if (callContent.Arguments is not null)
        {
            callContent.Arguments = new KernelArguments(callContent.Arguments);
        }

        var context = new AutoFunctionInvocationContext(new()
        {
            Function = function,
            Arguments = new(callContent.Arguments) { Services = this.FunctionInvocationServices },

            Messages = messages,
            Options = options,

            CallContent = callContent,
            Iteration = iteration,
            FunctionCallIndex = functionCallIndex,
            FunctionCount = callContents.Count,
        })
        { IsStreaming = isStreaming };

        object? result;
        try
        {
            result = await this.InvokeFunctionAsync(context, cancellationToken).ConfigureAwait(false);
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

    /// <summary>Creates one or more response messages for function invocation results.</summary>
    /// <param name="results">Information about the function call invocations and results.</param>
    /// <returns>A list of all chat messages created from <paramref name="results"/>.</returns>
    private IList<ChatMessage> CreateResponseMessages(List<FunctionInvocationResult> results)
    {
        var contents = new List<AIContent>(results.Count);
        for (int i = 0; i < results.Count; i++)
        {
            contents.Add(CreateFunctionResultContent(results[i]));
        }

        return [new(ChatRole.Tool, contents)];

        FunctionResultContent CreateFunctionResultContent(FunctionInvocationResult result)
        {
            Verify.NotNull(result);

            object? functionResult;
            if (result.Status == FunctionInvocationStatus.RanToCompletion)
            {
                functionResult = result.Result ?? "Success: Function completed.";
            }
            else
            {
                string message = result.Status switch
                {
                    FunctionInvocationStatus.NotFound => $"Error: Requested function \"{result.CallContent.Name}\" not found.",
                    FunctionInvocationStatus.Exception => "Error: Function failed.",
                    _ => "Error: Unknown error.",
                };

                if (this.IncludeDetailedErrors && result.Exception is not null)
                {
                    message = $"{message} Exception: {result.Exception.Message}";
                }

                functionResult = message;
            }

            return new FunctionResultContent(result.CallContent.CallId, functionResult) { Exception = result.Exception };
        }
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
    protected override async Task<(FunctionInvocationContextV2 context, object? result)> TryInvokeFunctionAsync(FunctionInvocationContextV2 context, CancellationToken cancellationToken)
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
            result = await context.Function.InvokeAsync(context.Arguments, cancellationToken).ConfigureAwait(false);
        }

        return (context, result);
    }
}
