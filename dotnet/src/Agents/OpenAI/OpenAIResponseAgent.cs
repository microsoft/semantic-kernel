// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Represents a <see cref="Agent"/> specialization based on OpenAI Response API.
/// </summary>
public sealed class OpenAIResponseAgent : Agent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgent"/> class.
    /// </summary>
    /// <param name="client">The OpenAI provider for accessing the Responses API service.</param>
    public OpenAIResponseAgent(OpenAIResponseClient client)
    {
        Verify.NotNull(client);

        this.Client = client;
    }

    /// <summary>
    /// Expose client for additional use.
    /// </summary>
    public OpenAIResponseClient Client { get; }

    /// <summary>
    /// Storing of messages is enabled.
    /// </summary>
    public bool StoreEnabled { get; init; } = false;

    /// <inheritdoc/>
   public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
    ICollection<ChatMessageContent> messages,
    AgentThread? thread = null,
    AgentInvokeOptions? options = null,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    Verify.NotNull(messages);

    AgentThread agentThread;
    OpenAIResponseAgentInvokeOptions extensionsContextOptions;
    IAsyncEnumerable<ChatMessageContent> invokeResults;

    try
    {
        agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);
        extensionsContextOptions = await this.FinalizeInvokeOptionsAsync(messages, options, agentThread, cancellationToken).ConfigureAwait(false);

        ChatHistory chatHistory = [.. messages];
        invokeResults = ResponseThreadActions.InvokeAsync(
            this,
            chatHistory,
            agentThread,
            extensionsContextOptions,
            cancellationToken);
    }
    catch (System.Net.Http.HttpRequestException ex) when (ex.Message.Contains("429"))
    {
        throw new KernelException($"Rate limit exceeded for agent '{this.Name}'. Check Retry-After header and implement backoff.", ex);
    }
    catch (System.Net.Http.HttpRequestException ex) when (ex.Message.Contains("401") || ex.Message.Contains("403"))
    {
        throw new KernelException($"Authentication or permission error for agent '{this.Name}'. Verify API key and account status.", ex);
    }
    catch (System.Net.Http.HttpRequestException ex) when (ex.Message.Contains("404"))
    {
        throw new KernelException($"Model or deployment not found for agent '{this.Name}'. Verify model configuration.", ex);
    }
    catch (System.Net.Http.HttpRequestException ex) when (ex.Message.Contains("content", StringComparison.OrdinalIgnoreCase) 
                                                          && (ex.Message.Contains("filter", StringComparison.OrdinalIgnoreCase) 
                                                          || ex.Message.Contains("policy", StringComparison.OrdinalIgnoreCase)))
    {
        throw new KernelException($"Content policy violation for agent '{this.Name}'. Request blocked by OpenAI filtering.", ex);
    }
    catch (TaskCanceledException ex) when (!cancellationToken.IsCancellationRequested)
    {
        throw new KernelException($"Request timeout for agent '{this.Name}'. The OpenAI API request timed out.", ex);
    }
    catch (Exception ex) when (ex.GetType().FullName?.StartsWith("OpenAI", StringComparison.OrdinalIgnoreCase) == true)
    {
        throw new KernelException($"OpenAI provider error for agent '{this.Name}': {ex.Message}", ex);
    }

    // Yield results with additional error handling
    await foreach (var result in invokeResults.ConfigureAwait(false))
    {
        await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);
        yield return new(result, agentThread);
    }
}

    /// <inheritdoc/>
   public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
    ICollection<ChatMessageContent> messages,
    AgentThread? thread = null,
    AgentInvokeOptions? options = null,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    Verify.NotNull(messages);

    AgentThread agentThread;
    OpenAIResponseAgentInvokeOptions extensionsContextOptions;
    ChatHistory chatHistory;
    int messageIndex;
    IAsyncEnumerable<StreamingChatMessageContent> invokeResults;

    try
    {
        agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);
        extensionsContextOptions = await this.FinalizeInvokeOptionsAsync(messages, options, agentThread, cancellationToken).ConfigureAwait(false);

        chatHistory = [.. messages];
        messageIndex = chatHistory.Count;
        invokeResults = ResponseThreadActions.InvokeStreamingAsync(
            this,
            chatHistory,
            agentThread,
            extensionsContextOptions,
            cancellationToken);
    }
    catch (System.Net.Http.HttpRequestException ex)
    {
        if (ex.Message.Contains("429"))
            throw new KernelException($"Rate limit exceeded for agent '{this.Name}' during streaming. Check Retry-After header and implement backoff.", ex);
        if (ex.Message.Contains("401") || ex.Message.Contains("403"))
            throw new KernelException($"Authentication or permission error for agent '{this.Name}' during streaming. Verify API key and account status.", ex);
        if (ex.Message.Contains("404"))
            throw new KernelException($"Model or deployment not found for agent '{this.Name}' during streaming. Verify model configuration.", ex);
        if (ex.Message.Contains("content", StringComparison.OrdinalIgnoreCase) 
            && (ex.Message.Contains("filter", StringComparison.OrdinalIgnoreCase) 
            || ex.Message.Contains("policy", StringComparison.OrdinalIgnoreCase)))
            throw new KernelException($"Content policy violation for agent '{this.Name}' during streaming. Request blocked by OpenAI filtering.", ex);

        throw;
    }
    catch (TaskCanceledException ex) when (!cancellationToken.IsCancellationRequested)
    {
        throw new KernelException($"Request timeout for agent '{this.Name}' during streaming. The OpenAI API request timed out.", ex);
    }
    catch (Exception ex) when (ex.GetType().FullName?.StartsWith("OpenAI", StringComparison.OrdinalIgnoreCase) == true)
    {
        throw new KernelException($"OpenAI provider error for agent '{this.Name}' during streaming: {ex.Message}", ex);
    }

    async Task NotifyMessagesAsync()
    {
        for (; messageIndex < chatHistory.Count; messageIndex++)
        {
            ChatMessageContent newMessage = chatHistory[messageIndex];
            await this.NotifyThreadOfNewMessage(agentThread, newMessage, cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(newMessage).ConfigureAwait(false);
            }
        }
    }

    await foreach (var result in invokeResults.ConfigureAwait(false))
    {
        await NotifyMessagesAsync().ConfigureAwait(false);
        yield return new(result, agentThread);
    }
}


    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    private async Task<AgentThread> EnsureThreadExistsWithMessagesAsync(ICollection<ChatMessageContent> messages, AgentThread? thread, CancellationToken cancellationToken)
    {
        if (this.StoreEnabled)
        {
            return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new OpenAIResponseAgentThread(this.Client), cancellationToken).ConfigureAwait(false);
        }

        return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new ChatHistoryAgentThread(), cancellationToken).ConfigureAwait(false);
    }

    private async Task<OpenAIResponseAgentInvokeOptions> FinalizeInvokeOptionsAsync(ICollection<ChatMessageContent> messages, AgentInvokeOptions? options, AgentThread agentThread, CancellationToken cancellationToken)
    {
        Kernel kernel = this.GetKernel(options);
#pragma warning disable SKEXP0110, SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        if (this.UseImmutableKernel)
        {
            kernel = kernel.Clone();
        }

        // Get the AIContextProviders contributions to the kernel.
        AIContext providersContext = await agentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);

        // Check for compatibility AIContextProviders and the UseImmutableKernel setting.
        if (providersContext.AIFunctions is { Count: > 0 } && !this.UseImmutableKernel)
        {
            throw new InvalidOperationException("AIContextProviders with AIFunctions are not supported when Agent UseImmutableKernel setting is false.");
        }

        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        string mergedAdditionalInstructions = FormatAdditionalInstructions(providersContext, options);
        OpenAIResponseAgentInvokeOptions extensionsContextOptions =
            options is null ?
                new()
                {
                    AdditionalInstructions = mergedAdditionalInstructions,
                    Kernel = kernel,
                } :
                new(options)
                {
                    AdditionalInstructions = mergedAdditionalInstructions,
                    Kernel = kernel,
                };
        return extensionsContextOptions;
    }
}
