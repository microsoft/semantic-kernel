// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Exceptions;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Represents a thread that contains messages.
/// </summary>
internal sealed class ChatThread : IAgentThread
{
    /// <inheritdoc/>
    public string Id { get; private set; }

    private readonly OpenAIRestContext _restContext;
    private bool _isDeleted;

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<IAgentThread> CreateAsync(OpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        // Common case is for failure exception to be raised by REST invocation.  Null result is a logical possibility, but unlikely edge case.
        var threadModel = await restContext.CreateThreadModelAsync(cancellationToken).ConfigureAwait(false);

        return new ChatThread(threadModel, messageListModel: null, restContext);
    }

    /// <summary>
    /// Retrieve an existing thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="ChatThread"> instance.</see></returns>
    public static async Task<IAgentThread> GetAsync(OpenAIRestContext restContext, string threadId, CancellationToken cancellationToken = default)
    {
        var threadModel = await restContext.GetThreadModelAsync(threadId, cancellationToken).ConfigureAwait(false);
        var messageListModel = await restContext.GetMessagesAsync(threadId, cancellationToken).ConfigureAwait(false);

        return new ChatThread(threadModel, messageListModel, restContext);
    }

    /// <inheritdoc/>
    public async Task<IChatMessage> AddUserMessageAsync(string message, CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        var messageModel =
            await this._restContext.CreateUserTextMessageAsync(
                this.Id,
                message,
                cancellationToken).ConfigureAwait(false);

        return new ChatMessage(messageModel);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<IChatMessage> InvokeAsync(IAgent agent, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        return this.InvokeAsync(agent, string.Empty, arguments, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<IChatMessage> InvokeAsync(IAgent agent, string userMessage, KernelArguments? arguments = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.ThrowIfDeleted();

        if (!string.IsNullOrWhiteSpace(userMessage))
        {
            yield return await this.AddUserMessageAsync(userMessage, cancellationToken).ConfigureAwait(false);
        }

        // Finalize prompt / agent instructions using provided parameters.
        var instructions = await agent.AsPromptTemplate().RenderAsync(agent.Kernel, arguments, cancellationToken).ConfigureAwait(false);

        // Create run using templated prompt
        var runModel = await this._restContext.CreateRunAsync(this.Id, agent.Id, instructions, agent.Tools, cancellationToken).ConfigureAwait(false);
        var run = new ChatRun(runModel, agent.Kernel, this._restContext);

        await foreach (var messageId in run.GetResultAsync(cancellationToken).ConfigureAwait(false))
        {
            var message = await this._restContext.GetMessageAsync(this.Id, messageId, cancellationToken).ConfigureAwait(false);
            yield return new ChatMessage(message);
        }
    }

    /// <summary>
    /// Delete an existing thread.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    public async Task DeleteAsync(CancellationToken cancellationToken)
    {
        if (this._isDeleted)
        {
            return;
        }

        await this._restContext.DeleteThreadModelAsync(this.Id, cancellationToken).ConfigureAwait(false);
        this._isDeleted = true;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatThread"/> class.
    /// </summary>
    private ChatThread(
        ThreadModel threadModel,
        ThreadMessageListModel? messageListModel,
        OpenAIRestContext restContext)
    {
        this.Id = threadModel.Id;
        this._restContext = restContext;
    }

    private void ThrowIfDeleted()
    {
        if (this._isDeleted)
        {
            throw new AgentException($"{nameof(ChatThread)}: {this.Id} has been deleted.");
        }
    }
}
