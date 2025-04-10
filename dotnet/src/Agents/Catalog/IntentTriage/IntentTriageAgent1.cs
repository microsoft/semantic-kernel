// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// An example <see cref="ServiceAgent"/> based on chat-completion and
/// two remote API's as tooling.
/// </summary>s
/// <remarks>
/// This agent invokes the language service API's directly
/// and only resorts to calling the LLM when there's no acceptable
/// result from the language services API's.
/// (Manual approach)
/// </remarks>
[ServiceAgentProvider<IntentTriageAgentProvider1>]
public sealed class IntentTriageAgent1 : ServiceAgent
{
    private readonly LanguagePlugin _plugin;
    private readonly IntentTriageLanguageSettings _settings;

    /// <summary>
    /// Initializes a new instance of the <see cref="IntentTriageAgent1"/> class.
    /// </summary>
    /// <param name="settings">Settings for usinge the language services.</param>
    public IntentTriageAgent1(IntentTriageLanguageSettings settings)
    {
        this.Description = IntentTriageAgentDefinition.Description;
        this._settings = settings;
        this._plugin = new LanguagePlugin(settings);
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatHistoryAgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        ChatMessageContent targetMessage = agentThread.ChatHistory.Last(message => !string.IsNullOrWhiteSpace(message.Content));
        string request = targetMessage.Content!;

        TriageResult triageResult = await this.InvokeLanguageServicesAsync(request);

        if (triageResult.TryGetQueryResult(this._settings.QueryThreshold, out string? queryResponse))
        {
            ChatMessageContent response = new(AuthorRole.Assistant, queryResponse);
            await this.NotifyThreadOfNewMessageAsync(agentThread, response, options, cancellationToken);
            yield return new AgentResponseItem<ChatMessageContent>(response, agentThread);
            yield break;
        }

        if (triageResult.TryGetAnalyzeResult(this._settings.AnalyzeThreshold, out string? analyzeResponse))
        {
            ChatMessageContent response = new(AuthorRole.Assistant, analyzeResponse);
            await this.NotifyThreadOfNewMessageAsync(agentThread, response, options, cancellationToken);
            yield return new AgentResponseItem<ChatMessageContent>(response, agentThread);
            yield break;
        }

        ChatCompletionAgent agent = this.GetAgent();
        IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> responses =
            agent.InvokeAsync(
                [new ChatMessageContent(AuthorRole.User, request)],
                agentThread,
                options,
                cancellationToken: cancellationToken);

        await foreach (AgentResponseItem<ChatMessageContent> response in responses)
        {
            yield return response;
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatHistoryAgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        ChatMessageContent targetMessage = agentThread.ChatHistory.Last(message => !string.IsNullOrWhiteSpace(message.Content));
        string request = targetMessage.Content!;

        TriageResult triageResult = await this.InvokeLanguageServicesAsync(request);

        if (triageResult.TryGetQueryResult(this._settings.QueryThreshold, out string? queryResponse))
        {
            StreamingChatMessageContent response = new(AuthorRole.Assistant, queryResponse);
            await this.NotifyThreadOfNewMessageAsync(agentThread, new ChatMessageContent(AuthorRole.Assistant, queryResponse), options, cancellationToken);
            yield return new AgentResponseItem<StreamingChatMessageContent>(response, agentThread);
            yield break;
        }

        if (triageResult.TryGetAnalyzeResult(this._settings.AnalyzeThreshold, out string? analyzeResponse))
        {
            StreamingChatMessageContent response = new(AuthorRole.Assistant, analyzeResponse);
            await this.NotifyThreadOfNewMessageAsync(agentThread, new ChatMessageContent(AuthorRole.Assistant, analyzeResponse), options, cancellationToken);
            yield return new AgentResponseItem<StreamingChatMessageContent>(response, agentThread);
            yield break;
        }

        ChatCompletionAgent agent = this.GetAgent();
        IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> responses =
            agent.InvokeStreamingAsync(
                [new ChatMessageContent(AuthorRole.User, request)],
                agentThread,
                options,
                cancellationToken: cancellationToken);

        await foreach (AgentResponseItem<StreamingChatMessageContent> response in responses)
        {
            yield return response;
        }
    }

    private ChatCompletionAgent GetAgent()
    {
        return
            new ChatCompletionAgent
            {
                Name = this.Name,
                Kernel = this.Kernel,
            };
    }

    private async Task<TriageResult> InvokeLanguageServicesAsync(string request)
    {
        ILogger<LanguagePlugin> logger = this.ActiveLoggerFactory.CreateLogger<LanguagePlugin>();
        Task<QualifiedResult?> analyzeTask = this._plugin.AnalyzeMessageAsync(request, logger);
        Task<QualifiedResult?> queryTask = this._plugin.QueryKnowledgeBaseAsync(request, logger);

        return
            new TriageResult
            {
                Analyze = await analyzeTask,
                Query = await queryTask,
            };
    }

    private async Task NotifyThreadOfNewMessageAsync(
        AgentThread thread,
        ChatMessageContent message,
        AgentInvokeOptions? options,
        CancellationToken cancellationToken)
    {
        await base.NotifyThreadOfNewMessage(thread, message, cancellationToken);
        if (options?.OnIntermediateMessage is not null)
        {
            await options.OnIntermediateMessage(message);
        }
    }
}
