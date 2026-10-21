// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit tests for <see cref="KernelProcess"/>.
/// </summary>
public class KernelProcessTests
{
    /// <summary>
    /// Verifies that the <see cref="KernelProcess"/> constructor assigns the supplied
    /// <c>threads</c> dictionary to the <see cref="KernelProcess.Threads"/> property
    /// instead of silently discarding it.
    /// </summary>
    [Fact]
    public void Constructor_AssignsThreadsParameter_WhenProvided()
    {
        // Arrange
        var state = new KernelProcessState(name: "TestProcess", version: "v1", id: "p1");
        var steps = new List<KernelProcessStepInfo>();
        var threads = new Dictionary<string, KernelProcessAgentThread>
        {
            ["main"] = new KernelProcessAgentThread { ThreadName = "main", ThreadId = "t-1" },
            ["aux"] = new KernelProcessAgentThread { ThreadName = "aux", ThreadId = "t-2" },
        };

        // Act
        var process = new KernelProcess(state, steps, edges: null, threads: threads);

        // Assert
        Assert.Equal(2, process.Threads.Count);
        Assert.True(process.Threads.ContainsKey("main"));
        Assert.True(process.Threads.ContainsKey("aux"));
        Assert.Equal("t-1", process.Threads["main"].ThreadId);
        Assert.Equal("t-2", process.Threads["aux"].ThreadId);
    }

    /// <summary>
    /// Verifies that the <see cref="KernelProcess"/> constructor leaves
    /// <see cref="KernelProcess.Threads"/> as an empty dictionary when the
    /// <c>threads</c> argument is null.
    /// </summary>
    [Fact]
    public void Constructor_DefaultsThreadsToEmptyDictionary_WhenNull()
    {
        // Arrange
        var state = new KernelProcessState(name: "TestProcess", version: "v1", id: "p2");
        var steps = new List<KernelProcessStepInfo>();

        // Act
        var process = new KernelProcess(state, steps, edges: null, threads: null);

        // Assert
        Assert.NotNull(process.Threads);
        Assert.Empty(process.Threads);
    }
}
