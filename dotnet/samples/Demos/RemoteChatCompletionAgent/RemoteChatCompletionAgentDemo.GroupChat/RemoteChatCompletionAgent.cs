// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace RemoteChatCompletionAgentDemo.GroupChat;

/// <summary>
/// Defines a remote chat completion agent.
/// </summary>
public sealed class RemoteChatCompletionAgent : ChatHistoryAgent
{
    private readonly RemoteAgentHttpClient _client;

    /// <summary>
    /// Instantiates a new instance of the <see cref="RemoteChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="client">The client for interacting with a remote agent.</param>
    public RemoteChatCompletionAgent(RemoteAgentHttpClient client)
    {
        this._client = client ?? throw new ArgumentNullException(nameof(client));

        var agentDetails = this.GetAgentDetailsAsync().GetAwaiter().GetResult();
        this.Name = agentDetails.Name;
        this.Instructions = agentDetails.Instructions;
    }

    /// <summary>
    /// Gets the role used for agent instructions.  Defaults to "system".
    /// </summary>
    /// <remarks>
    /// Certain versions of "O*" series (deep reasoning) models require the instructions
    /// to be provided as "developer" role.  Other versions support neither role and
    /// an agent targeting such a model cannot provide instructions.  Agent functionality
    /// will be dictated entirely by the provided plugins.
    /// </remarks>
    public AuthorRole InstructionsRole { get; init; } = AuthorRole.System;

    /// <summary>
    /// Query the remote agent details.
    /// </summary>
    public async Task<AgentDetails> GetAgentDetailsAsync()
    {
        await this._client.GetAgentDetailsAsync().ConfigureAwait(false);
        var response = this._client.GetAgentDetailsAsync().Result;

        return JsonSerializer.Deserialize<AgentDetails>(await response.Content.ReadAsStringAsync().ConfigureAwait(false))!;
    }

    /// <inheritdoc/>
    [Obsolete("Base contract defines method as obsolete")]
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(ChatHistory history, KernelArguments? arguments = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var response = await this._client.InvokeAsync(history, cancellationToken).ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            var result = JsonSerializer.Deserialize<ChatMessageContent>(content);
            if (result != null)
            {
                yield return result;
            }
        }
        else
        {
            throw new Exception($"Failed to invoke agent: {response.ReasonPhrase}");
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        var invokeResults = this.InternalInvokeAsync(
            chatHistoryAgentThread,
            options?.KernelArguments,
            options?.Kernel,
            options?.AdditionalInstructions,
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            // 1. During AutoInvoke = true, the function call content is provided via the callback
            // above, since it is not returned as part of the regular response to the user.
            // 2. During AutoInvoke = false, the function call content is returned directly as a
            // regular response here.
            // 3. If the user Terminates the function call, via a filter, the function call content
            // is also returned as part of the regular response here.
            //
            // In the first case, we don't want to add the function call content to the thread here
            // since it should already have been added in the callback above.
            // In the second case, we shouldn't add the function call content to the thread, since
            // we don't know if the user will execute the call. They should add it themselves.
            // In the third case, we don't want to add the function call content to the thread either,
            // since the filter terminated the call, and therefore won't get executed.
            if (!result.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, result, cancellationToken).ConfigureAwait(false);

                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(result).ConfigureAwait(false);
                }
            }

            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    [Obsolete("Base contract defines method as obsolete")]
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(ChatHistory history, KernelArguments? arguments = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var response = await this._client.InvokeStreamingAsync(history, cancellationToken).ConfigureAwait(false);

        if (response.IsSuccessStatusCode)
        {
            var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            using var reader = new StreamReader(stream);

            while (!reader.EndOfStream && !cancellationToken.IsCancellationRequested)
            {
                var line = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
                if (!string.IsNullOrWhiteSpace(line))
                {
                    var result = JsonSerializer.Deserialize<StreamingChatMessageContent>(line);
                    if (result != null)
                    {
                        yield return result;
                    }
                }
            }
        }
        else
        {
            throw new Exception($"Failed to invoke streaming agent: {response.ReasonPhrase}");
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var chatHistoryAgentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new ChatHistoryAgentThread(),
            cancellationToken).ConfigureAwait(false);

        var invokeResults = this.InternalInvokeStreamingAsync(
            chatHistoryAgentThread,
            async (m) =>
            {
                await this.NotifyThreadOfNewMessage(chatHistoryAgentThread, m, cancellationToken).ConfigureAwait(false);
                if (options?.OnIntermediateMessage is not null)
                {
                    await options.OnIntermediateMessage(m).ConfigureAwait(false);
                }
            },
            options?.KernelArguments,
            options?.Kernel,
            options?.AdditionalInstructions,
            cancellationToken);

        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, chatHistoryAgentThread);
        }
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    private async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        ChatHistoryAgentThread history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        string? additionalInstructions = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;

        var response = await this._client.InvokeAsync(history.ChatHistory, cancellationToken).ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            var result = JsonSerializer.Deserialize<ChatMessageContent>(content);
            if (result != null)
            {
                yield return result;
            }
        }
    }

    private async IAsyncEnumerable<StreamingChatMessageContent> InternalInvokeStreamingAsync(
        ChatHistoryAgentThread history,
        Func<ChatMessageContent, Task> onNewMessage,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        string? additionalInstructions = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        kernel ??= this.Kernel;

        AuthorRole? role = null;
        StringBuilder builder = new();
        var response = await this._client.InvokeStreamingAsync(history.ChatHistory, cancellationToken).ConfigureAwait(false);
        if (response.IsSuccessStatusCode)
        {
            var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            using var reader = new StreamReader(stream);

            while (!reader.EndOfStream && !cancellationToken.IsCancellationRequested)
            {
                var line = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
                if (!string.IsNullOrWhiteSpace(line))
                {
                    var result = JsonSerializer.Deserialize<StreamingChatMessageContent>(line);
                    if (result != null)
                    {
                        role = result.Role;
                        yield return result;
                    }
                }
            }
        }

        // Do not duplicate terminated function result to history
        if (role != AuthorRole.Tool)
        {
            await onNewMessage(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name }).ConfigureAwait(false);
            history.ChatHistory.Add(new(role ?? AuthorRole.Assistant, builder.ToString()) { AuthorName = this.Name });
        }
    }
}

/// <summary>
/// Http client for remote agent.
/// </summary>
/// <param name="httpClient">An inner client</param>
public class RemoteAgentHttpClient(HttpClient httpClient)
{
    /// <summary>
    /// Get agent details.
    /// </summary>
    public Task<HttpResponseMessage> GetAgentDetailsAsync(CancellationToken cancellationToken = default)
    {
#pragma warning disable CA2234 // We cannot pass uri here since we are using a customer http client with a base address
        return httpClient.GetAsync("/agent/details", cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided history.
    /// </summary>
    public Task<HttpResponseMessage> InvokeAsync(ChatHistory history, CancellationToken cancellationToken = default)
    {
#pragma warning disable CA2234 // We cannot pass uri here since we are using a customer http client with a base address
        return httpClient.PostAsync("/agent/invoke", new StringContent(JsonSerializer.Serialize(history), Encoding.UTF8, "application/json"), cancellationToken);
    }

    /// <summary>
    /// Invoke the agent with the provided history and stream the response.
    /// </summary>
    public Task<HttpResponseMessage> InvokeStreamingAsync(ChatHistory history, CancellationToken cancellationToken = default)
    {
#pragma warning disable CA2234 // We cannot pass uri here since we are using a customer http client with a base address
        return httpClient.PostAsync("/agent/invoke-streaming", new StringContent(JsonSerializer.Serialize(history), Encoding.UTF8, "application/json"), cancellationToken);
    }
}

/// <summary>
/// Describes the remote agent
/// </summary>
public class AgentDetails
{
    /// <summary>
    /// The agent name.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The agent instructions.
    /// </summary>
    public string Instructions { get; set; } = string.Empty;
}
