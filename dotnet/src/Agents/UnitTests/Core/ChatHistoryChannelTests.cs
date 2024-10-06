<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
<<<<<<< HEAD
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
>>>>>>> Stashed changes
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatHistoryChannel"/>.
/// </summary>
public class ChatHistoryChannelTests
{
    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> throws if passed an agent that
    /// does not implement <see cref="ChatHistoryKernelAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentWithoutIChatHistoryHandlerAsync()
    {
        // Arrange
        Mock<Agent> agent = new(); // Not a IChatHistoryHandler
        ChatHistoryChannel channel = new(); // Requires IChatHistoryHandler

        // Act & Assert
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
=======
        Mock<Agent> agent = new(); // Not a IChatHistoryHandler
        ChatHistoryChannel channel = new(); // Requires IChatHistoryHandler
>>>>>>> main
>>>>>>> Stashed changes
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAsync(agent.Object).ToArrayAsync().AsTask());
    }
}
