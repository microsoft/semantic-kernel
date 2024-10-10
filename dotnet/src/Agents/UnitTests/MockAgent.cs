<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
using System.Threading;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Mock definition of <see cref="KernelAgent"/> with a <see cref="ChatHistoryKernelAgent"/> contract.
/// </summary>
internal class MockAgent : ChatHistoryKernelAgent
{
    public int InvokeCount { get; private set; }

    public IReadOnlyList<ChatMessageContent> Response { get; set; } = [];

    public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;

        return this.Response.ToAsyncEnumerable();
    }

    public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.InvokeCount++;
        return this.Response.Select(m => new StreamingChatMessageContent(m.Role, m.Content)).ToAsyncEnumerable();
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

    /// <inheritdoc/>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(ChatHistoryChannel).FullName!;
    }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        ChatHistoryChannel channel =
            new()
            {
                Logger = this.LoggerFactory.CreateLogger<ChatHistoryChannel>()
            };

        return Task.FromResult<AgentChannel>(channel);
    }

    protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        ChatHistory history =
            JsonSerializer.Deserialize<ChatHistory>(channelState) ??
            throw new KernelException("Unable to restore channel: invalid state.");
        return Task.FromResult<AgentChannel>(new ChatHistoryChannel(history));
    // Expose protected method for testing
    public new KernelArguments? MergeArguments(KernelArguments? arguments)
    {
        return base.MergeArguments(arguments);
    }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
