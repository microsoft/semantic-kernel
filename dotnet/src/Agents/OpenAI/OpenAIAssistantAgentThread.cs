// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Represents a conversation thread for an Open AI Assistant agent.
/// </summary>
public sealed class OpenAIAssistantAgentThread : AgentThread
{
    private readonly bool _useThreadConstructorExtension = false;
    private readonly AssistantClient _client;

    private readonly ThreadCreationOptions? _options;

    private readonly IEnumerable<ChatMessageContent>? _messages;
    private readonly IReadOnlyList<string>? _codeInterpreterFileIds;
    private readonly string? _vectorStoreId;
    private readonly IReadOnlyDictionary<string, string>? _metadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentThread"/> class.
    /// </summary>
    /// <param name="client">The assistant client to use for interacting with threads.</param>
    public OpenAIAssistantAgentThread(AssistantClient client)
    {
        Verify.NotNull(client);

        this._client = client;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentThread"/> class.
    /// </summary>
    /// <param name="client">The assistant client to use for interacting with threads.</param>
    /// <param name="options">The options to use when creating the thread.</param>
    public OpenAIAssistantAgentThread(AssistantClient client, ThreadCreationOptions options)
    {
        Verify.NotNull(client);

        this._client = client;
        this._options = options;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentThread"/> class.
    /// </summary>
    /// <param name="client">The assistant client to use for interacting with threads.</param>
    /// <param name="messages">The initial messages for the thread.</param>
    /// <param name="codeInterpreterFileIds">The file IDs for the code interpreter tool.</param>
    /// <param name="vectorStoreId">The vector store identifier.</param>
    /// <param name="metadata">The metadata for the thread.</param>
    public OpenAIAssistantAgentThread(
        AssistantClient client,
        IEnumerable<ChatMessageContent>? messages = null,
        IReadOnlyList<string>? codeInterpreterFileIds = null,
        string? vectorStoreId = null,
        IReadOnlyDictionary<string, string>? metadata = null)
    {
        Verify.NotNull(client);

        this._useThreadConstructorExtension = true;

        this._client = client;
        this._messages = messages;
        this._codeInterpreterFileIds = codeInterpreterFileIds;
        this._vectorStoreId = vectorStoreId;
        this._metadata = metadata;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentThread"/> class that resumes an existing thread.
    /// </summary>
    /// <param name="client">The assistant client to use for interacting with threads.</param>
    /// <param name="id">The ID of an existing thread to resume.</param>
    public OpenAIAssistantAgentThread(AssistantClient client, string id)
    {
        Verify.NotNull(client);
        Verify.NotNull(id);

        this._client = client;
        this.Id = id;
    }

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been created.</returns>
    public new Task CreateAsync(CancellationToken cancellationToken = default)
    {
        return base.CreateAsync(cancellationToken);
    }

    /// <inheritdoc />
    protected async override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        const string ErrorMessage = "The thread could not be created due to an error response from the service.";

        try
        {
            if (this._useThreadConstructorExtension)
            {
                return await this._client.CreateThreadAsync(this._messages, this._codeInterpreterFileIds, this._vectorStoreId, this._metadata, cancellationToken: cancellationToken).ConfigureAwait(false);
            }

            var assistantThreadResponse = await this._client.CreateThreadAsync(this._options, cancellationToken: cancellationToken).ConfigureAwait(false);
            return assistantThreadResponse.Value.Id;
        }
        catch (ClientResultException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
        catch (AggregateException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
    }

    /// <inheritdoc />
    protected override async Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        const string ErrorMessage = "The thread could not be deleted due to an error response from the service.";

        try
        {
            await this._client.DeleteThreadAsync(this.Id, cancellationToken).ConfigureAwait(false);
        }
        catch (ClientResultException ex) when (ex.Status == 404)
        {
            // Do nothing, since the thread was already deleted.
        }
        catch (ClientResultException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
        catch (AggregateException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
    }

    /// <inheritdoc />
    protected override async Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        const string ErrorMessage = "The message could not be added to the thread due to an error response from the service.";

        // If the message was generated by this agent, it is already in the thread and we shouldn't add it again.
        if (newMessage.Metadata == null || !newMessage.Metadata.TryGetValue("ThreadId", out var messageThreadId) || !string.Equals(messageThreadId, this.Id))
        {
            try
            {
                await AssistantThreadActions.CreateMessageAsync(this._client, this.Id!, newMessage, cancellationToken).ConfigureAwait(false);
            }
            catch (ClientResultException ex)
            {
                throw new AgentThreadOperationException(ErrorMessage, ex);
            }
            catch (AggregateException ex)
            {
                throw new AgentThreadOperationException(ErrorMessage, ex);
            }
        }
    }

    /// <summary>
    /// Asynchronously retrieves all messages in the thread.
    /// </summary>
    /// <param name="sortOrder">The order to return messages in.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The messages in the thread.</returns>
    /// <exception cref="InvalidOperationException">The thread has been deleted.</exception>
    [Experimental("SKEXP0110")]
    public async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(MessageCollectionOrder? sortOrder = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this.Id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        await foreach (var message in AssistantThreadActions.GetMessagesAsync(this._client, this.Id!, sortOrder, cancellationToken).ConfigureAwait(false))
        {
            yield return message;
        }
    }
}
