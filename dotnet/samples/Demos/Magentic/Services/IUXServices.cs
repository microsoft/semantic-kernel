// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Magentic.Services;

/// <summary>
/// Defines a common interface for user interaction.
/// </summary>
public interface IUXServices // %%% TODO: Consider
{
    /// <summary>
    /// Defines a signature for soliciting textual input.
    /// </summary>
    /// <returns>The input text.</returns>
    ValueTask<string?> ReadInputAsync();

    /// <summary>
    /// Defines a signature for displaying the inner agent chat.
    /// </summary>
    ValueTask DisplayChatAsync(ChatMessageContent message);

    /// <summary>
    /// Defines a signature for displaying the messages to the user.
    /// </summary>
    ValueTask DisplayOutputAsync(ChatMessageContent message);

    ///// <summary>
    ///// Defines a signature for displaying task progress.
    ///// </summary>
    //ValueTask DisplayProgressAsync(ChatMessages.Progress message);
}
