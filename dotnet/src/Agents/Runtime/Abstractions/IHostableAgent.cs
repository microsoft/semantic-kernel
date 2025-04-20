// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.AgentRuntime;

/// <summary>
/// Represents an agent that can be explicitly hosted and closed when the runtime shuts down.
/// </summary>
public interface IHostableAgent : IAgent
{
    /// <summary>
    /// Called when the runtime is closing.
    /// </summary>
    /// <returns>A task representing the asynchronous operation.</returns>
    ValueTask CloseAsync();
}
