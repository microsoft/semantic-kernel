// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization bound to a <see cref="ChatHistoryChannel"/>.
/// </summary>
public abstract class ChatHistoryKernelAgent : KernelAgent, IChatHistoryHandler
{
    private readonly ILogger _logger;
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistoryKernelAgent"/> class.
    /// </summary>
    protected ChatHistoryKernelAgent()
    {
        this._loggerFactory = this.Kernel.LoggerFactory;
        this._logger = this._loggerFactory.CreateLogger<ChatHistoryKernelAgent>();
    }

    /// <inheritdoc/>
    protected internal sealed override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(ChatHistoryChannel).FullName;
    }

    /// <inheritdoc/>
    protected internal sealed override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        this._logger.LogDebug("Create channel for {AgentName}...", this.Name);
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel());
    }

    /// <inheritdoc/>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        IReadOnlyList<ChatMessageContent> history,
        CancellationToken cancellationToken = default);
}
