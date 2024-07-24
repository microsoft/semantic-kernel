// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents;

namespace AgentWithHistoryTruncation;

internal class TruncatingChatAgent : ChatCompletionAgent
{
    /// <summary>
    /// %%%
    /// </summary>
    public TruncationStrategy? TruncationStrategy { get; init; }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(TruncatingChatChannel).FullName!;
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        TruncatingChatChannel channel =
            new()
            {
                Logger = this.LoggerFactory.CreateLogger<ChatHistoryChannel>()
            };

        return Task.FromResult<AgentChannel>(channel);
    }
}
