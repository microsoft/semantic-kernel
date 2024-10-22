// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.FunctionCalling;

/// <summary>
/// Class responsible for providing function calling configuration and processing AI function calls. As part of the processing, it will:
/// 1. Iterate over <see cref="FunctionCallContent"/> items representing AI model function calls in the <see cref="ChatMessageContent.Items"/> collection.
/// 2. Look up each function in the <see cref="Kernel"/>.
/// 3. Invoke the auto function invocation filter, if registered, for each function.
/// 4. Invoke each function and add the function result to the <see cref="ChatHistory"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class FunctionCallsProcessor
{
    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertize itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 128;

    /// <summary>
    /// The maximum number of function auto-invokes that can be made in a single user request.
    /// </summary>
    /// <remarks>
    /// After this number of iterations as part of a single user request is reached, auto-invocation
    /// will be disabled. This is a safeguard against possible runaway execution if the model routinely re-requests
    /// the same function over and over.
    /// </remarks>
    private const int MaximumAutoInvokeAttempts = 128;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    /// <remarks>
    /// It is temporarily made internal to allow code that uses the old function model to read it and decide whether to continue auto-invocation or not.
    /// It should be made private when the old model is deprecated.
    /// Despite the field being static, its value is unique per execution flow. So if thousands of requests hit it in parallel, each request will see its unique value.
    /// </remarks>
    internal static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>
    /// The logger.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionCallsProcessor"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    public FunctionCallsProcessor(ILogger? logger = null)
    {
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    /// Retrieves the configuration of the specified <see cref="FunctionChoiceBehavior"/>.
    /// </summary>
    /// <param name="behavior">The function choice behavior.</param>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="requestIndex">Request sequence index.</param>
    /// <param name="kernel">The <see cref="Kernel"/>.</param>
    /// <returns>The configuration of the specified <see cref="FunctionChoiceBehavior"/>.</returns>
    public FunctionChoiceBehaviorConfiguration? GetConfiguration(FunctionChoiceBehavior? behavior, ChatHistory chatHistory, int requestIndex, Kernel? kernel)
    {
        // If no behavior is specified, return null.
        if (behavior is null)
        {
            return null;
        }

        var configuration = behavior.GetConfiguration(new(chatHistory) { Kernel = kernel, RequestSequenceIndex = requestIndex });

        // Disable auto invocation if no kernel is provided.
        configuration.AutoInvoke = kernel is not null && configuration.AutoInvoke;

        // Disable auto invocation if we've exceeded the allowed auto-invoke limit.
        int maximumAutoInvokeAttempts = configuration.AutoInvoke ? MaximumAutoInvokeAttempts : 0;
        if (requestIndex >= maximumAutoInvokeAttempts)
        {
            configuration.AutoInvoke = false;
            if (this._logger!.IsEnabled(LogLevel.Debug))
            {
                this._logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", maximumAutoInvokeAttempts);
            }
        }
        // Disable auto invocation if we've exceeded the allowed limit of in-flight auto-invokes. See XML comment for the "MaxInflightAutoInvokes" const for more details.
        else if (s_inflightAutoInvokes.Value >= MaxInflightAutoInvokes)
        {
            configuration.AutoInvoke = false;
            if (this._logger!.IsEnabled(LogLevel.Debug))
            {
                this._logger.LogDebug("Maximum auto-invoke ({MaxInflightAutoInvoke}) reached.", MaxInflightAutoInvokes);
            }
        }

        if (configuration.Functions?.Count == 0)
        {
            this._logger.LogDebug("No functions provided to AI model. Function calling is disabled.");
        }

        return configuration;
    }

    /// <summary>
    /// Processes AI function calls by iterating over the function calls, invoking them and adding the results to the chat history.
    /// </summary>
    /// <param name="chatMessageContent">The chat message content representing AI model response and containing function calls.</param>
    /// <param name="chatHistory">The chat history to add function invocation results to.</param>
    /// <param name="requestIndex">AI model function(s) call request sequence index.</param>
    /// <param name="checkIfFunctionAdvertised">Callback to check if a function was advertised to AI model or not.</param>
    /// <param name="options">Function choice behavior options.</param>
    /// <param name="kernel">The <see cref="Kernel"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>Last chat history message if function invocation filter requested processing termination, otherwise null.</returns>
    public async Task<ChatMessageContent?> ProcessFunctionCallsAsync(
        ChatMessageContent chatMessageContent,
        ChatHistory chatHistory,
        int requestIndex,
        Func<FunctionCallContent, bool> checkIfFunctionAdvertised,
        FunctionChoiceBehaviorOptions options,
        Kernel? kernel,
        CancellationToken cancellationToken)
    {
        var functionCalls = FunctionCallContent.GetFunctionCalls(chatMessageContent).ToList();

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Function calls: {Calls}", functionCalls.Count);
        }
        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            var messages = new List<string>(functionCalls.Count);
            foreach (var call in functionCalls)
            {
                var argumentsString = call.Arguments is not null ? $"({string.Join(",", call.Arguments.Select(a => $"{a.Key}={a.Value}"))})" : "()";
                var pluginName = string.IsNullOrEmpty(call.PluginName) ? string.Empty : $"{call.PluginName}-";
                messages.Add($"{pluginName}{call.FunctionName}{argumentsString}");
            }
            this._logger.LogTrace("Function calls: {Calls}", string.Join(", ", messages));
        }

        // Add the result message to the caller's chat history;
        // this is required for AI model to understand the function results.
        chatHistory.Add(chatMessageContent);

        var functionTasks = options.AllowConcurrentInvocation && functionCalls.Count > 1 ?
            new List<Task<(string? Result, string? ErrorMessage, FunctionCallContent FunctionCall, bool Terminate)>>(functionCalls.Count) :
            null;

        // We must send back a result for every function call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
        for (int functionCallIndex = 0; functionCallIndex < functionCalls.Count; functionCallIndex++)
        {
            FunctionCallContent functionCall = functionCalls[functionCallIndex];

            // Check if the function call has an exception.
            if (functionCall.Exception is not null)
            {
                this.AddFunctionCallResultToChatHistory(chatHistory, functionCall, result: null, errorMessage: $"Error: Function call processing failed. {functionCall.Exception.Message}");
                continue;
            }

            // Make sure the requested function is one of the functions that was advertised to the AI model.
            if (!checkIfFunctionAdvertised(functionCall))
            {
                this.AddFunctionCallResultToChatHistory(chatHistory, functionCall, result: null, errorMessage: "Error: Function call request for a function that wasn't defined.");
                continue;
            }

            // Look up the function in the kernel
            if (!kernel!.Plugins.TryGetFunction(functionCall.PluginName, functionCall.FunctionName, out KernelFunction? function))
            {
                this.AddFunctionCallResultToChatHistory(chatHistory, functionCall, result: null, errorMessage: "Error: Requested function could not be found.");
                continue;
            }

            // Prepare context for the auto function invocation filter and invoke it.
            AutoFunctionInvocationContext invocationContext = new(kernel, function, new(function) { Culture = kernel.Culture }, chatHistory, chatMessageContent)
            {
                Arguments = functionCall.Arguments,
                RequestSequenceIndex = requestIndex,
                FunctionSequenceIndex = functionCallIndex,
                FunctionCount = functionCalls.Count
            };

            var functionTask = Task.Run<(string? Result, string? ErrorMessage, FunctionCallContent FunctionCall, bool Terminate)>(async () =>
            {
                s_inflightAutoInvokes.Value++;
                try
                {
                    invocationContext = await OnAutoFunctionInvocationAsync(kernel, invocationContext, async (context) =>
                    {
                        // Check if filter requested termination.
                        if (context.Terminate)
                        {
                            return;
                        }

                        // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                        // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                        // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                        context.Result = await function.InvokeAsync(kernel, invocationContext.Arguments, cancellationToken: cancellationToken).ConfigureAwait(false);
                    }).ConfigureAwait(false);
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031 // Do not catch general exception types
                {
                    return (null, $"Error: Exception while invoking function. {e.Message}", functionCall, false);
                }

                // Apply any changes from the auto function invocation filters context to final result.
                var stringResult = ProcessFunctionResult(invocationContext.Result.GetValue<object>() ?? string.Empty);
                return (stringResult, null, functionCall, invocationContext.Terminate);
            }, cancellationToken);

            // If concurrent invocation is enabled, add the task to the list for later waiting. Otherwise, join with it now.
            if (functionTasks is not null)
            {
                functionTasks.Add(functionTask);
            }
            else
            {
                var functionResult = await functionTask.ConfigureAwait(false);
                this.AddFunctionCallResultToChatHistory(chatHistory, functionResult.FunctionCall, functionResult.Result, functionResult.ErrorMessage);

                // If filter requested termination, return last chat history message.
                if (functionResult.Terminate)
                {
                    this._logger.LogDebug("Filter requested termination of automatic function invocation.");
                    return chatHistory.Last();
                }
            }
        }

        // If concurrent invocation is enabled, join with all the tasks now.
        if (functionTasks is not null)
        {
            bool terminationRequested = false;

            // Wait for all of the function invocations to complete, then add the results to the chat, but stop when we hit a
            // function for which termination was requested.
            await Task.WhenAll(functionTasks).ConfigureAwait(false);
            foreach (var functionTask in functionTasks)
            {
                this.AddFunctionCallResultToChatHistory(chatHistory, functionTask.Result.FunctionCall, functionTask.Result.Result, functionTask.Result.ErrorMessage);

                if (functionTask.Result.Terminate)
                {
                    terminationRequested = true;
                }
            }

            // If filter requested termination, return last chat history message.
            if (terminationRequested)
            {
                this._logger.LogDebug("Filter requested termination of automatic function invocation.");
                return chatHistory.Last();
            }
        }

        return null;
    }

    /// <summary>
    /// Adds the function call result or error message to the chat history.
    /// </summary>
    /// <param name="chatHistory">The chat history to add the function call result to.</param>
    /// <param name="functionCall">The function call.</param>
    /// <param name="result">The function result to add to the chat history.</param>
    /// <param name="errorMessage">The error message to add to the chat history.</param>
    private void AddFunctionCallResultToChatHistory(ChatHistory chatHistory, FunctionCallContent functionCall, string? result, string? errorMessage = null)
    {
        // Log any error
        if (errorMessage is not null && this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Failed to handle function request ({Id}). {Error}", functionCall.Id, errorMessage);
        }

        result ??= errorMessage ?? string.Empty;

        var message = new ChatMessageContent(role: AuthorRole.Tool, content: result);
        message.Items.Add(new FunctionResultContent(functionCall.FunctionName, functionCall.PluginName, functionCall.Id, result));

        chatHistory.Add(message);
    }

    /// <summary>
    /// Invokes the auto function invocation filters.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/>.</param>
    /// <param name="context">The auto function invocation context.</param>
    /// <param name="functionCallCallback">The function to call after the filters.</param>
    /// <returns>The auto function invocation context.</returns>
    private static async Task<AutoFunctionInvocationContext> OnAutoFunctionInvocationAsync(
        Kernel kernel,
        AutoFunctionInvocationContext context,
        Func<AutoFunctionInvocationContext, Task> functionCallCallback)
    {
        await InvokeFilterOrFunctionAsync(kernel.AutoFunctionInvocationFilters, functionCallCallback, context).ConfigureAwait(false);

        return context;
    }

    /// <summary>
    /// This method will execute auto function invocation filters and function recursively.
    /// If there are no registered filters, just function will be executed.
    /// If there are registered filters, filter on <paramref name="index"/> position will be executed.
    /// Second parameter of filter is callback. It can be either filter on <paramref name="index"/> + 1 position or function if there are no remaining filters to execute.
    /// Function will be always executed as last step after all filters.
    /// </summary>
    private static async Task InvokeFilterOrFunctionAsync(
        IList<IAutoFunctionInvocationFilter>? autoFunctionInvocationFilters,
        Func<AutoFunctionInvocationContext, Task> functionCallCallback,
        AutoFunctionInvocationContext context,
        int index = 0)
    {
        if (autoFunctionInvocationFilters is { Count: > 0 } && index < autoFunctionInvocationFilters.Count)
        {
            await autoFunctionInvocationFilters[index].OnAutoFunctionInvocationAsync(context,
                (context) => InvokeFilterOrFunctionAsync(autoFunctionInvocationFilters, functionCallCallback, context, index + 1)).ConfigureAwait(false);
        }
        else
        {
            await functionCallCallback(context).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Processes the function result.
    /// </summary>
    /// <param name="functionResult">The result of the function call.</param>
    /// <returns>A string representation of the function result.</returns>
    public static string? ProcessFunctionResult(object functionResult)
    {
        if (functionResult is string stringResult)
        {
            return stringResult;
        }

        // This is an optimization to use ChatMessageContent content directly  
        // without unnecessary serialization of the whole message content class.  
        if (functionResult is ChatMessageContent chatMessageContent)
        {
            return chatMessageContent.ToString();
        }

        return JsonSerializer.Serialize(functionResult);
    }
}
