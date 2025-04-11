// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

#pragma warning disable CA2213 // Disposable fields should be disposed
#pragma warning disable IDE0009 // Use explicit 'this.' qualifier
#pragma warning disable IDE1006 // Missing prefix: 's_'

namespace Microsoft.SemanticKernel.ChatCompletion;

// Slight modified source from
// https://raw.githubusercontent.com/dotnet/extensions/refs/heads/main/src/Libraries/Microsoft.Extensions.AI/ChatCompletion/FunctionInvokingChatClient.cs

/// <summary>
/// A delegating chat client that invokes functions defined on <see cref="ChatOptions"/>.
/// Include this in a chat pipeline to resolve function calls automatically.
/// </summary>
/// <remarks>
/// <para>
/// When this client receives a <see cref="Microsoft.Extensions.AI.FunctionCallContent"/> in a chat response, it responds
/// by calling the corresponding <see cref="AIFunction"/> defined in <see cref="ChatOptions"/>,
/// producing a <see cref="FunctionResultContent"/>.
/// </para>
/// <para>
/// The provided implementation of <see cref="IChatClient"/> is thread-safe for concurrent use so long as the
/// <see cref="AIFunction"/> instances employed as part of the supplied <see cref="ChatOptions"/> are also safe.
/// The <see cref="AllowConcurrentInvocation"/> property can be used to control whether multiple function invocation
/// requests as part of the same request are invocable concurrently, but even with that set to <see langword="false"/>
/// (the default), multiple concurrent requests to this same instance and using the same tools could result in those
/// tools being used concurrently (one per request). For example, a function that accesses the HttpContext of a specific
/// ASP.NET web request should only be used as part of a single <see cref="ChatOptions"/> at a time, and only with
/// <see cref="AllowConcurrentInvocation"/> set to <see langword="false"/>, in case the inner client decided to issue multiple
/// invocation requests to that same function.
/// </para>
/// </remarks>
[ExcludeFromCodeCoverage]
internal sealed partial class KernelFunctionInvokingChatClient : DelegatingChatClient
{
    /// <summary>The <see cref="KernelFunctionInvocationContext"/> for the current function invocation.</summary>
    private static readonly AsyncLocal<KernelFunctionInvocationContext?> s_currentContext = new();

    /// <summary>The logger to use for logging information about function invocation.</summary>
    private readonly ILogger _logger;

    /// <summary>The <see cref="ActivitySource"/> to use for telemetry.</summary>
    /// <remarks>This component does not own the instance and should not dispose it.</remarks>
    private readonly ActivitySource? _activitySource;

    /// <summary>Maximum number of roundtrips allowed to the inner client.</summary>
    private int? _maximumIterationsPerRequest;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunctionInvokingChatClient"/> class.
    /// </summary>
    /// <param name="innerClient">The underlying <see cref="IChatClient"/>, or the next instance in a chain of clients.</param>
    /// <param name="logger">An <see cref="ILogger"/> to use for logging information about function invocation.</param>
    public KernelFunctionInvokingChatClient(IChatClient innerClient, ILogger? logger = null)
        : base(innerClient)
    {
        this._logger = logger ?? NullLogger.Instance;
        this._activitySource = innerClient.GetService<ActivitySource>();
    }

    /// <summary>
    /// Gets or sets the <see cref="KernelFunctionInvocationContext"/> for the current function invocation.
    /// </summary>
    /// <remarks>
    /// This value flows across async calls.
    /// </remarks>
    internal static KernelFunctionInvocationContext? CurrentContext
    {
        get => s_currentContext.Value;
        set => s_currentContext.Value = value;
    }

    /// <summary>
    /// Gets or sets a value indicating whether to handle exceptions that occur during function calls.
    /// </summary>
    /// <value>
    /// <see langword="false"/> if the
    /// underlying <see cref="IChatClient"/> will be instructed to give a response without invoking
    /// any further functions if a function call fails with an exception.
    /// <see langword="true"/> if the underlying <see cref="IChatClient"/> is allowed
    /// to continue attempting function calls until <see cref="MaximumIterationsPerRequest"/> is reached.
    /// The default value is <see langword="false"/>.
    /// </value>
    /// <remarks>
    /// Changing the value of this property while the client is in use might result in inconsistencies
    /// whether errors are retried during an in-flight request.
    /// </remarks>
    public bool RetryOnError { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether detailed exception information should be included
    /// in the chat history when calling the underlying <see cref="IChatClient"/>.
    /// </summary>
    /// <value>
    /// <see langword="true"/> if the full exception message is added to the chat history
    /// when calling the underlying <see cref="IChatClient"/>.
    /// <see langword="false"/> if a generic error message is included in the chat history.
    /// The default value is <see langword="false"/>.
    /// </value>
    /// <remarks>
    /// <para>
    /// Setting the value to <see langword="false"/> prevents the underlying language model from disclosing
    /// raw exception details to the end user, since it doesn't receive that information. Even in this
    /// case, the raw <see cref="Exception"/> object is available to application code by inspecting
    /// the <see cref="Microsoft.Extensions.AI.FunctionResultContent.Exception"/> property.
    /// </para>
    /// <para>
    /// Setting the value to <see langword="true"/> can help the underlying <see cref="IChatClient"/> bypass problems on
    /// its own, for example by retrying the function call with different arguments. However it might
    /// result in disclosing the raw exception information to external users, which can be a security
    /// concern depending on the application scenario.
    /// </para>
    /// <para>
    /// Changing the value of this property while the client is in use might result in inconsistencies
    /// as to whether detailed errors are provided during an in-flight request.
    /// </para>
    /// </remarks>
    public bool IncludeDetailedErrors { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether to allow concurrent invocation of functions.
    /// </summary>
    /// <value>
    /// <see langword="true"/> if multiple function calls can execute in parallel.
    /// <see langword="false"/> if function calls are processed serially.
    /// The default value is <see langword="false"/>.
    /// </value>
    /// <remarks>
    /// An individual response from the inner client might contain multiple function call requests.
    /// By default, such function calls are processed serially. Set <see cref="AllowConcurrentInvocation"/> to
    /// <see langword="true"/> to enable concurrent invocation such that multiple function calls can execute in parallel.
    /// </remarks>
    public bool AllowConcurrentInvocation { get; set; }

    /// <summary>
    /// Gets or sets the maximum number of iterations per request.
    /// </summary>
    /// <value>
    /// The maximum number of iterations per request.
    /// The default value is <see langword="null"/>.
    /// </value>
    /// <remarks>
    /// <para>
    /// Each request to this <see cref="KernelFunctionInvokingChatClient"/> might end up making
    /// multiple requests to the inner client. Each time the inner client responds with
    /// a function call request, this client might perform that invocation and send the results
    /// back to the inner client in a new request. This property limits the number of times
    /// such a roundtrip is performed. If null, there is no limit applied. If set, the value
    /// must be at least one, as it includes the initial request.
    /// </para>
    /// <para>
    /// Changing the value of this property while the client is in use might result in inconsistencies
    /// as to how many iterations are allowed for an in-flight request.
    /// </para>
    /// </remarks>
    public int? MaximumIterationsPerRequest
    {
        get => this._maximumIterationsPerRequest;
        set
        {
            if (value < 1)
            {
                throw new ArgumentOutOfRangeException(nameof(value));
            }

            this._maximumIterationsPerRequest = value;
        }
    }

    /// <inheritdoc/>
    public override async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        // A single request into this GetResponseAsync may result in multiple requests to the inner client.
        // Create an activity to group them together for better observability.
        using Activity? activity = this._activitySource?.StartActivity(nameof(KernelFunctionInvokingChatClient));

        // Copy the original messages in order to avoid enumerating the original messages multiple times.
        // The IEnumerable can represent an arbitrary amount of work.
        List<ChatMessage> originalMessages = [.. messages];
        messages = originalMessages;

        List<ChatMessage>? augmentedHistory = null; // the actual history of messages sent on turns other than the first
        ChatResponse? response = null; // the response from the inner client, which is possibly modified and then eventually returned
        List<ChatMessage>? responseMessages = null; // tracked list of messages, across multiple turns, to be used for the final response
        UsageDetails? totalUsage = null; // tracked usage across all turns, to be used for the final response
        List<Microsoft.Extensions.AI.FunctionCallContent>? functionCallContents = null; // function call contents that need responding to in the current turn
        bool lastIterationHadThreadId = false; // whether the last iteration's response had a ChatThreadId set

        for (int iteration = 0; ; iteration++)
        {
            functionCallContents?.Clear();

            // Make the call to the inner client.
            response = await base.GetResponseAsync(messages, options, cancellationToken).ConfigureAwait(false);
            if (response is null)
            {
                throw new InvalidOperationException($"The inner {nameof(IChatClient)} returned a null {nameof(ChatResponse)}.");
            }

            // Any function call work to do? If yes, ensure we're tracking that work in functionCallContents.
            bool requiresFunctionInvocation =
                options?.Tools is { Count: > 0 } &&
                (!this.MaximumIterationsPerRequest.HasValue || iteration < this.MaximumIterationsPerRequest.GetValueOrDefault()) &&
                CopyFunctionCalls(response.Messages, ref functionCallContents);

            // In a common case where we make a request and there's no function calling work required,
            // fast path out by just returning the original response.
            if (iteration == 0 && !requiresFunctionInvocation)
            {
                return response;
            }

            // Track aggregatable details from the response, including all of the response messages and usage details.
            (responseMessages ??= []).AddRange(response.Messages);
            if (response.Usage is not null)
            {
                if (totalUsage is not null)
                {
                    totalUsage.Add(response.Usage);
                }
                else
                {
                    totalUsage = response.Usage;
                }
            }

            // If there are no tools to call, or for any other reason we should stop, we're done.
            // Break out of the loop and allow the handling at the end to configure the response
            // with aggregated data from previous requests.
            if (!requiresFunctionInvocation)
            {
                break;
            }

            // Prepare the history for the next iteration.
            FixupHistories(originalMessages, ref messages, ref augmentedHistory, response, responseMessages, ref lastIterationHadThreadId);

            // Prepare the options for the next auto function invocation iteration.
            UpdateOptionsForAutoFunctionInvocation(ref options!, response.Messages.Last().ToChatMessageContent(), isStreaming: false);

            // Add the responses from the function calls into the augmented history and also into the tracked
            // list of response messages.
            var modeAndMessages = await this.ProcessFunctionCallsAsync(augmentedHistory, options!, functionCallContents!, iteration, isStreaming: false, cancellationToken).ConfigureAwait(false);
            responseMessages.AddRange(modeAndMessages.MessagesAdded);

            // Clear the auto function invocation options.
            ClearOptionsForAutoFunctionInvocation(ref options!);

            if (UpdateOptionsForMode(modeAndMessages.Mode, ref options!, response.ChatThreadId))
            {
                // Terminate
                break;
            }
        }

        Debug.Assert(responseMessages is not null, "Expected to only be here if we have response messages.");
        response.Messages = responseMessages!;
        response.Usage = totalUsage;

        return response;
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
        IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        // A single request into this GetStreamingResponseAsync may result in multiple requests to the inner client.
        // Create an activity to group them together for better observability.
        using Activity? activity = this._activitySource?.StartActivity(nameof(KernelFunctionInvokingChatClient));

        // Copy the original messages in order to avoid enumerating the original messages multiple times.
        // The IEnumerable can represent an arbitrary amount of work.
        List<ChatMessage> originalMessages = [.. messages];
        messages = originalMessages;

        List<ChatMessage>? augmentedHistory = null; // the actual history of messages sent on turns other than the first
        List<Microsoft.Extensions.AI.FunctionCallContent>? functionCallContents = null; // function call contents that need responding to in the current turn
        List<ChatMessage>? responseMessages = null; // tracked list of messages, across multiple turns, to be used in fallback cases to reconstitute history
        bool lastIterationHadThreadId = false; // whether the last iteration's response had a ChatThreadId set
        List<ChatResponseUpdate> updates = []; // updates from the current response

        for (int iteration = 0; ; iteration++)
        {
            updates.Clear();
            functionCallContents?.Clear();

            await foreach (var update in base.GetStreamingResponseAsync(messages, options, cancellationToken).ConfigureAwait(false))
            {
                if (update is null)
                {
                    throw new InvalidOperationException($"The inner {nameof(IChatClient)} streamed a null {nameof(ChatResponseUpdate)}.");
                }

                updates.Add(update);

                _ = CopyFunctionCalls(update.Contents, ref functionCallContents);

                yield return update;
                Activity.Current = activity; // workaround for https://github.com/dotnet/runtime/issues/47802
            }

            // If there are no tools to call, or for any other reason we should stop, return the response.
            if (functionCallContents is not { Count: > 0 } ||
                options?.Tools is not { Count: > 0 } ||
                (this.MaximumIterationsPerRequest is { } maxIterations && iteration >= maxIterations))
            {
                break;
            }

            // Reconstitute a response from the response updates.
            var response = updates.ToChatResponse();
            (responseMessages ??= []).AddRange(response.Messages);

            // Prepare the history for the next iteration.
            FixupHistories(originalMessages, ref messages, ref augmentedHistory, response, responseMessages, ref lastIterationHadThreadId);

            // Prepare the options for the next auto function invocation iteration.
            UpdateOptionsForAutoFunctionInvocation(ref options!, response.Messages.Last().ToChatMessageContent(), isStreaming: true);

            // Process all the functions, adding their results into the history.
            var modeAndMessages = await this.ProcessFunctionCallsAsync(augmentedHistory, options, functionCallContents, iteration, isStreaming: true, cancellationToken).ConfigureAwait(false);
            responseMessages.AddRange(modeAndMessages.MessagesAdded);

            // Clear the auto function invocation options.
            ClearOptionsForAutoFunctionInvocation(ref options!);

            // Stream any generated function results. This mirrors what's done for GetResponseAsync, where the returned messages
            // include all activities, including generated function results.
            string toolResponseId = Guid.NewGuid().ToString("N");
            foreach (var message in modeAndMessages.MessagesAdded)
            {
                var toolResultUpdate = new ChatResponseUpdate
                {
                    AdditionalProperties = message.AdditionalProperties,
                    AuthorName = message.AuthorName,
                    ChatThreadId = response.ChatThreadId,
                    CreatedAt = DateTimeOffset.UtcNow,
                    Contents = message.Contents,
                    RawRepresentation = message.RawRepresentation,
                    ResponseId = toolResponseId,
                    Role = message.Role,
                };

                yield return toolResultUpdate;
                Activity.Current = activity; // workaround for https://github.com/dotnet/runtime/issues/47802
            }

            if (UpdateOptionsForMode(modeAndMessages.Mode, ref options, response.ChatThreadId))
            {
                // Terminate
                yield break;
            }
        }
    }

    /// <summary>Prepares the various chat message lists after a response from the inner client and before invoking functions.</summary>
    /// <param name="originalMessages">The original messages provided by the caller.</param>
    /// <param name="messages">The messages reference passed to the inner client.</param>
    /// <param name="augmentedHistory">The augmented history containing all the messages to be sent.</param>
    /// <param name="response">The most recent response being handled.</param>
    /// <param name="allTurnsResponseMessages">A list of all response messages received up until this point.</param>
    /// <param name="lastIterationHadThreadId">Whether the previous iteration's response had a thread id.</param>
    private static void FixupHistories(
        IEnumerable<ChatMessage> originalMessages,
        ref IEnumerable<ChatMessage> messages,
        [NotNull] ref List<ChatMessage>? augmentedHistory,
        ChatResponse response,
        List<ChatMessage> allTurnsResponseMessages,
        ref bool lastIterationHadThreadId)
    {
        // We're now going to need to augment the history with function result contents.
        // That means we need a separate list to store the augmented history.
        if (response.ChatThreadId is not null)
        {
            // The response indicates the inner client is tracking the history, so we don't want to send
            // anything we've already sent or received.
            if (augmentedHistory is not null)
            {
                augmentedHistory.Clear();
            }
            else
            {
                augmentedHistory = [];
            }

            lastIterationHadThreadId = true;
        }
        else if (lastIterationHadThreadId)
        {
            // In the very rare case where the inner client returned a response with a thread ID but then
            // returned a subsequent response without one, we want to reconstitute the full history. To do that,
            // we can populate the history with the original chat messages and then all of the response
            // messages up until this point, which includes the most recent ones.
            augmentedHistory ??= [];
            augmentedHistory.Clear();
            augmentedHistory.AddRange(originalMessages);
            augmentedHistory.AddRange(allTurnsResponseMessages);

            lastIterationHadThreadId = false;
        }
        else
        {
            // If augmentedHistory is already non-null, then we've already populated it with everything up
            // until this point (except for the most recent response). If it's null, we need to seed it with
            // the chat history provided by the caller.
            augmentedHistory ??= originalMessages.ToList();

            // Now add the most recent response messages.
            augmentedHistory.AddMessages(response);

            lastIterationHadThreadId = false;
        }

        // Use the augmented history as the new set of messages to send.
        messages = augmentedHistory;
    }

    /// <summary>Copies any <see cref="FunctionCallContent"/> from <paramref name="messages"/> to <paramref name="functionCalls"/>.</summary>
    private static bool CopyFunctionCalls(
        IList<ChatMessage> messages, [NotNullWhen(true)] ref List<Microsoft.Extensions.AI.FunctionCallContent>? functionCalls)
    {
        bool any = false;
        int count = messages.Count;
        for (int i = 0; i < count; i++)
        {
            any |= CopyFunctionCalls(messages[i].Contents, ref functionCalls);
        }

        return any;
    }

    /// <summary>Copies any <see cref="Microsoft.Extensions.AI.FunctionCallContent"/> from <paramref name="content"/> to <paramref name="functionCalls"/>.</summary>
    private static bool CopyFunctionCalls(
        IList<AIContent> content, [NotNullWhen(true)] ref List<Microsoft.Extensions.AI.FunctionCallContent>? functionCalls)
    {
        bool any = false;
        int count = content.Count;
        for (int i = 0; i < count; i++)
        {
            if (content[i] is Microsoft.Extensions.AI.FunctionCallContent functionCall)
            {
                (functionCalls ??= []).Add(functionCall);
                any = true;
            }
        }

        return any;
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

    /// <summary>Updates <paramref name="options"/> for the response.</summary>
    /// <returns>true if the function calling loop should terminate; otherwise, false.</returns>
    private static bool UpdateOptionsForMode(ContinueMode mode, ref ChatOptions options, string? chatThreadId)
    {
        switch (mode)
        {
            case ContinueMode.Continue when options.ToolMode is RequiredChatToolMode:
                // We have to reset the tool mode to be non-required after the first iteration,
                // as otherwise we'll be in an infinite loop.
                options = options.Clone();
                options.ToolMode = null;
                options.ChatThreadId = chatThreadId;

                break;

            case ContinueMode.AllowOneMoreRoundtrip:
                // The LLM gets one further chance to answer, but cannot use tools.
                options = options.Clone();
                options.Tools = null;
                options.ToolMode = null;
                options.ChatThreadId = chatThreadId;

                break;

            case ContinueMode.Terminate:
                // Bail immediately.
                return true;

            default:
                // As with the other modes, ensure we've propagated the chat thread ID to the options.
                // We only need to clone the options if we're actually mutating it.
                if (options.ChatThreadId != chatThreadId)
                {
                    options = options.Clone();
                    options.ChatThreadId = chatThreadId;
                }

                break;
        }

        return false;
    }

    /// <summary>
    /// Processes the function calls in the <paramref name="functionCallContents"/> list.
    /// </summary>
    /// <param name="messages">The current chat contents, inclusive of the function call contents being processed.</param>
    /// <param name="options">The options used for the response being processed.</param>
    /// <param name="functionCallContents">The function call contents representing the functions to be invoked.</param>
    /// <param name="iteration">The iteration number of how many roundtrips have been made to the inner client.</param>
    /// <param name="isStreaming">Whether the function calls are being processed in a streaming context.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>A <see cref="ContinueMode"/> value indicating how the caller should proceed.</returns>
    private async Task<(ContinueMode Mode, IList<ChatMessage> MessagesAdded)> ProcessFunctionCallsAsync(
        List<ChatMessage> messages, ChatOptions options, List<Microsoft.Extensions.AI.FunctionCallContent> functionCallContents, int iteration, bool isStreaming, CancellationToken cancellationToken)
    {
        // We must add a response for every tool call, regardless of whether we successfully executed it or not.
        // If we successfully execute it, we'll add the result. If we don't, we'll add an error.

        Debug.Assert(functionCallContents.Count > 0, "Expected at least one function call.");
        ContinueMode continueMode = ContinueMode.Continue;

        // Process all functions. If there's more than one and concurrent invocation is enabled, do so in parallel.
        if (functionCallContents.Count == 1)
        {
            FunctionInvocationResult result = await this.ProcessFunctionCallAsync(
                messages, options, functionCallContents, iteration, 0, isStreaming, cancellationToken).ConfigureAwait(false);

            IList<ChatMessage> added = this.CreateResponseMessages([result]);
            this.ThrowIfNoFunctionResultsAdded(added);

            messages.AddRange(added);
            return (result.ContinueMode, added);
        }
        else
        {
            List<FunctionInvocationResult> results = [];

            var terminationRequested = false;
            if (this.AllowConcurrentInvocation)
            {
                // Schedule the invocation of every function.
                results.AddRange(await Task.WhenAll(
                    from i in Enumerable.Range(0, functionCallContents.Count)
                    select Task.Run(() => this.ProcessFunctionCallAsync(
                        messages, options, functionCallContents,
                        iteration, i, isStreaming, cancellationToken))).ConfigureAwait(false));

                terminationRequested = results.Any(r => r.ContinueMode == ContinueMode.Terminate);
            }
            else
            {
                // Invoke each function serially.
                for (int i = 0; i < functionCallContents.Count; i++)
                {
                    var result = await this.ProcessFunctionCallAsync(
                        messages, options, functionCallContents,
                        iteration, i, isStreaming, cancellationToken).ConfigureAwait(false);

                    results.Add(result);

                    if (result.ContinueMode == ContinueMode.Terminate)
                    {
                        continueMode = ContinueMode.Terminate;
                        terminationRequested = true;
                        break;
                    }
                }
            }

            IList<ChatMessage> added = this.CreateResponseMessages(results);
            this.ThrowIfNoFunctionResultsAdded(added);
            messages.AddRange(added);

            if (!terminationRequested)
            {
                // If any function requested termination, we'll terminate.
                continueMode = ContinueMode.Continue;
                foreach (FunctionInvocationResult fir in results)
                {
                    if (fir.ContinueMode > continueMode)
                    {
                        continueMode = fir.ContinueMode;
                    }
                }
            }

            return (continueMode, added);
        }
    }

    /// <summary>
    /// Throws an exception if <see cref="CreateResponseMessages"/> doesn't create any messages.
    /// </summary>
    private void ThrowIfNoFunctionResultsAdded(IList<ChatMessage>? messages)
    {
        if (messages is null || messages.Count == 0)
        {
            throw new InvalidOperationException($"{this.GetType().Name}.{nameof(this.CreateResponseMessages)} returned null or an empty collection of messages.");
        }
    }

    /// <summary>Processes the function call described in <paramref name="callContents"/>[<paramref name="iteration"/>].</summary>
    /// <param name="messages">The current chat contents, inclusive of the function call contents being processed.</param>
    /// <param name="options">The options used for the response being processed.</param>
    /// <param name="callContents">The function call contents representing all the functions being invoked.</param>
    /// <param name="iteration">The iteration number of how many roundtrips have been made to the inner client.</param>
    /// <param name="functionCallIndex">The 0-based index of the function being called out of <paramref name="callContents"/>.</param>
    /// <param name="isStreaming">Whether the function calls are being processed in a streaming context.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>A <see cref="ContinueMode"/> value indicating how the caller should proceed.</returns>
    private async Task<FunctionInvocationResult> ProcessFunctionCallAsync(
        List<ChatMessage> messages, ChatOptions options, List<Microsoft.Extensions.AI.FunctionCallContent> callContents,
        int iteration, int functionCallIndex, bool isStreaming, CancellationToken cancellationToken)
    {
        var callContent = callContents[functionCallIndex];

        // Look up the AIFunction for the function call. If the requested function isn't available, send back an error.
        AIFunction? function = options.Tools!.OfType<AIFunction>().FirstOrDefault(
            t => t.Name == callContent.Name);
        if (function is null)
        {
            return new(ContinueMode.Continue, FunctionInvocationStatus.NotFound, callContent, result: null, exception: null);
        }

        if (callContent.Arguments is not null)
        {
            callContent.Arguments = new KernelArguments(callContent.Arguments);
        }

        var context = new AutoFunctionInvocationContext(options)
        {
            Messages = messages,
            CallContent = callContent,
            AIFunction = function,
            Iteration = iteration,
            FunctionCallIndex = functionCallIndex,
            FunctionCount = callContents.Count,
            IsStreaming = isStreaming
        };

        object? result;
        try
        {
            result = await this.InvokeFunctionAsync(context, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e) when (!cancellationToken.IsCancellationRequested)
        {
            return new(this.RetryOnError ? ContinueMode.Continue : ContinueMode.AllowOneMoreRoundtrip, // We won't allow further function calls, hence the LLM will just get one more chance to give a final answer.
                FunctionInvocationStatus.Exception,
                callContent,
                result: null,
                exception: e);
        }

        return new(
            context.Terminate ? ContinueMode.Terminate : ContinueMode.Continue,
            FunctionInvocationStatus.RanToCompletion,
            callContent,
            result,
            exception: null);
    }

    /// <summary>Represents the return value of <see cref="ProcessFunctionCallsAsync"/>, dictating how the loop should behave.</summary>
    /// <remarks>These values are ordered from least severe to most severe, and code explicitly depends on the ordering.</remarks>
    internal enum ContinueMode
    {
        /// <summary>Send back the responses and continue processing.</summary>
        Continue = 0,

        /// <summary>Send back the response but without any tools.</summary>
        AllowOneMoreRoundtrip = 1,

        /// <summary>Immediately exit the function calling loop.</summary>
        Terminate = 2,
    }

    /// <summary>Creates one or more response messages for function invocation results.</summary>
    /// <param name="results">Information about the function call invocations and results.</param>
    /// <returns>A list of all chat messages created from <paramref name="results"/>.</returns>
    internal IList<ChatMessage> CreateResponseMessages(
        IReadOnlyList<FunctionInvocationResult> results)
    {
        var contents = new List<AIContent>(results.Count);
        for (int i = 0; i < results.Count; i++)
        {
            contents.Add(CreateFunctionResultContent(results[i]));
        }

        return [new(ChatRole.Tool, contents)];

        Microsoft.Extensions.AI.FunctionResultContent CreateFunctionResultContent(FunctionInvocationResult result)
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

            return new Microsoft.Extensions.AI.FunctionResultContent(result.CallContent.CallId, functionResult) { Exception = result.Exception };
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
    /// Function will be always executed as last step after all filters.
    /// </summary>
    private async Task InvokeFilterOrFunctionAsync(
        Func<AutoFunctionInvocationContext, Task> functionCallCallback,
        AutoFunctionInvocationContext context,
        int index = 0)
    {
        IList<IAutoFunctionInvocationFilter>? autoFunctionInvocationFilters = context.Kernel.AutoFunctionInvocationFilters;

        if (autoFunctionInvocationFilters is { Count: > 0 } && index < autoFunctionInvocationFilters.Count)
        {
            await autoFunctionInvocationFilters[index].OnAutoFunctionInvocationAsync(
                context,
                (context) => this.InvokeFilterOrFunctionAsync(functionCallCallback, context, index + 1)
            ).ConfigureAwait(false);
        }
        else
        {
            await functionCallCallback(context).ConfigureAwait(false);
        }
    }

    /// <summary>Invokes the function asynchronously.</summary>
    /// <param name="invocationContext">The function invocation context detailing the function to be invoked and its arguments along with additional request information.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function invocation, or <see langword="null"/> if the function invocation returned <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="invocationContext"/> is <see langword="null"/>.</exception>
    internal async Task<object?> InvokeFunctionAsync(KernelFunctionInvocationContext invocationContext, CancellationToken cancellationToken)
    {
        Verify.NotNull(invocationContext);

        using Activity? activity = this._activitySource?.StartActivity(invocationContext.AIFunction.Name);

        long startingTimestamp = 0;
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            startingTimestamp = Stopwatch.GetTimestamp();
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this.LogInvokingSensitive(invocationContext.AIFunction.Name, LoggingAsJson(invocationContext.CallContent.Arguments, invocationContext.AIFunction.JsonSerializerOptions));
            }
            else
            {
                this.LogInvoking(invocationContext.AIFunction.Name);
            }
        }

        object? result = null;
        try
        {
            CurrentContext = invocationContext;
            if (invocationContext is AutoFunctionInvocationContext autoFunctionInvocationContext)
            {
                autoFunctionInvocationContext = await this.OnAutoFunctionInvocationAsync(
                    autoFunctionInvocationContext,
                    async (context) =>
                    {
                        // Check if filter requested termination
                        if (context.Terminate)
                        {
                            return;
                        }

                        // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                        // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                        // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                        result = await invocationContext.AIFunction.InvokeAsync(autoFunctionInvocationContext.Arguments, cancellationToken).ConfigureAwait(false);
                        context.Result = new FunctionResult(context.Function, result);
                    }).ConfigureAwait(false);
                result = autoFunctionInvocationContext.Result.GetValue<object>();
            }
        }
        catch (Exception e)
        {
            if (activity is not null)
            {
                _ = activity.SetTag("error.type", e.GetType().FullName)
                            .SetStatus(ActivityStatusCode.Error, e.Message);
            }

            if (e is OperationCanceledException)
            {
                this.LogInvocationCanceled(invocationContext.AIFunction.Name);
            }
            else
            {
                this.LogInvocationFailed(invocationContext.AIFunction.Name, e);
            }

            throw;
        }
        finally
        {
            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                TimeSpan elapsed = GetElapsedTime(startingTimestamp);

                if (result is not null && this._logger.IsEnabled(LogLevel.Trace))
                {
                    this.LogInvocationCompletedSensitive(invocationContext.AIFunction.Name, elapsed, LoggingAsJson(result, invocationContext.AIFunction.JsonSerializerOptions));
                }
                else
                {
                    this.LogInvocationCompleted(invocationContext.AIFunction.Name, elapsed);
                }
            }
        }

        return result;
    }

    /// <summary>Serializes <paramref name="value"/> as JSON for logging purposes.</summary>
    private static string LoggingAsJson<T>(T value, JsonSerializerOptions? options)
    {
        if (options?.TryGetTypeInfo(typeof(T), out var typeInfo) is true ||
            AIJsonUtilities.DefaultOptions.TryGetTypeInfo(typeof(T), out typeInfo))
        {
#pragma warning disable CA1031 // Do not catch general exception types
            try
            {
                return JsonSerializer.Serialize(value, typeInfo);
            }
            catch
            {
            }
#pragma warning restore CA1031 // Do not catch general exception types
        }

        // If we're unable to get a type info for the value, or if we fail to serialize,
        // return an empty JSON object. We do not want lack of type info to disrupt application behavior with exceptions.
        return "{}";
    }

    private static TimeSpan GetElapsedTime(long startingTimestamp) =>
#if NET
        Stopwatch.GetElapsedTime(startingTimestamp);
#else
        new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * ((double)TimeSpan.TicksPerSecond / Stopwatch.Frequency)));
#endif

    [LoggerMessage(LogLevel.Debug, "Invoking {MethodName}.", SkipEnabledCheck = true)]
    private partial void LogInvoking(string methodName);

    [LoggerMessage(LogLevel.Trace, "Invoking {MethodName}({Arguments}).", SkipEnabledCheck = true)]
    private partial void LogInvokingSensitive(string methodName, string arguments);

    [LoggerMessage(LogLevel.Debug, "{MethodName} invocation completed. Duration: {Duration}", SkipEnabledCheck = true)]
    private partial void LogInvocationCompleted(string methodName, TimeSpan duration);

    [LoggerMessage(LogLevel.Trace, "{MethodName} invocation completed. Duration: {Duration}. Result: {Result}", SkipEnabledCheck = true)]
    private partial void LogInvocationCompletedSensitive(string methodName, TimeSpan duration, string result);

    [LoggerMessage(LogLevel.Debug, "{MethodName} invocation canceled.")]
    private partial void LogInvocationCanceled(string methodName);

    [LoggerMessage(LogLevel.Error, "{MethodName} invocation failed.")]
    private partial void LogInvocationFailed(string methodName, Exception error);

    /// <summary>Provides information about the invocation of a function call.</summary>
    public sealed class FunctionInvocationResult
    {
        internal FunctionInvocationResult(ContinueMode continueMode, FunctionInvocationStatus status, Microsoft.Extensions.AI.FunctionCallContent callContent, object? result, Exception? exception)
        {
            this.ContinueMode = continueMode;
            this.Status = status;
            this.CallContent = callContent;
            this.Result = result;
            this.Exception = exception;
        }

        /// <summary>Gets status about how the function invocation completed.</summary>
        public FunctionInvocationStatus Status { get; }

        /// <summary>Gets the function call content information associated with this invocation.</summary>
        public Microsoft.Extensions.AI.FunctionCallContent CallContent { get; }

        /// <summary>Gets the result of the function call.</summary>
        public object? Result { get; }

        /// <summary>Gets any exception the function call threw.</summary>
        public Exception? Exception { get; }

        /// <summary>Gets an indication for how the caller should continue the processing loop.</summary>
        internal ContinueMode ContinueMode { get; }
    }

    /// <summary>Provides error codes for when errors occur as part of the function calling loop.</summary>
    public enum FunctionInvocationStatus
    {
        /// <summary>The operation completed successfully.</summary>
        RanToCompletion,

        /// <summary>The requested function could not be found.</summary>
        NotFound,

        /// <summary>The function call failed with an exception.</summary>
        Exception,
    }
}
