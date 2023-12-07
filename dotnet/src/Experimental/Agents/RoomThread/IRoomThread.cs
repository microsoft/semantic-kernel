// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.RoomThread;

/// <summary>
/// Interface representing a room thread.
/// </summary>
public interface IRoomThread
{
    /// <summary>
    /// Adds the user message to the discussion.
    /// </summary>
    /// <param name="message">The user message.</param>
    /// <returns></returns>
    Task AddUserMessageAsync(string message);

    /// <summary>
    /// Event produced when an agent sends a message.
    /// </summary>
    event EventHandler<string>? OnMessageReceived;
}
