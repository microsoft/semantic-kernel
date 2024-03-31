// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

public class AgentExceptionTests
{
    [Fact]
    public void VerifyAgentException()
    {
        Assert.Throws<AgentException>(this.ThrowException);
        Assert.Throws<AgentException>(() => this.ThrowException("test"));
        Assert.Throws<AgentException>(() => this.ThrowWrappedException("test"));
    }

    private void ThrowException()
    {
        throw new AgentException();
    }

    private void ThrowException(string message)
    {
        throw new AgentException(message);
    }

    private void ThrowWrappedException(string message)
    {
        throw new AgentException(message, new InvalidOperationException());
    }
}
