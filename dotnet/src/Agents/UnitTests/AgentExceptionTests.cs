// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentException"/>.
/// </summary>
public class AgentExceptionTests
{
    /// <summary>
    /// Exercise usage of the various constructors.
    /// </summary>
    [Fact]
    public void VerifyAgentExceptionThrown()
    {
        Assert.Throws<AgentException>(this.ThrowException);
        Assert.Throws<AgentException>(() => this.ThrowException("test"));
        Assert.Throws<AgentException>(() => this.ThrowWrappedException("test"));
    }

    private void ThrowException()
    {
        try
        {
            throw new AgentException();
        }
        catch (AgentException exception)
        {
            Assert.NotNull(exception.Message);
            Assert.Null(exception.InnerException);
            throw;
        }
    }

    private void ThrowException(string message)
    {
        try
        {
            throw new AgentException(message);
        }
        catch (AgentException exception)
        {
            Assert.Equivalent(message, exception.Message);
            Assert.Null(exception.InnerException);
            throw;
        }
    }

    private void ThrowWrappedException(string message)
    {
        try
        {
            throw new AgentException(message, new InvalidOperationException());
        }
        catch (AgentException exception)
        {
            Assert.Equivalent(message, exception.Message);
            Assert.NotNull(exception.InnerException);
            throw;
        }
    }
}
