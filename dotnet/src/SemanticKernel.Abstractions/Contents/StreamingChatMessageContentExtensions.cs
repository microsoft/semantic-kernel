// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for <see cref="StreamingChatMessageContent"/>.</summary>
[Experimental("SKEXP0001")]
public static class StreamingChatMessageContentExtensions
{
    /// <summary>Converts a <see cref="StreamingChatMessageContent"/> to a <see cref="ChatResponseUpdate"/>.</summary>
    /// <remarks>
    /// <para>This conversion should not be necessary once SK eventually adopts the shared content types.</para>
    /// <para>
    /// Each <see cref="StreamingFunctionCallUpdateContent"/> is converted on its own, as if it were a complete function call.
    /// Streamed function call arguments usually arrive as fragments that must be combined before they can be parsed, so
    /// arguments that are not valid JSON are reported through <see cref="Microsoft.Extensions.AI.FunctionCallContent.Exception"/>
    /// instead of being thrown.
    /// </para>
    /// </remarks>
    public static ChatResponseUpdate ToChatResponseUpdate(this StreamingChatMessageContent content)
        => StreamingChatMessageContentConverter.ToChatResponseUpdate(content);
}
