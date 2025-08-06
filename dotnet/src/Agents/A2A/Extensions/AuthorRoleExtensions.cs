// Copyright (c) Microsoft. All rights reserved.

using System;
using A2A;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.A2A;

/// <summary>
/// Extensions for converting between <see cref="MessageRole"/> amd <see cref="AuthorRole"/>.
/// </summary>
internal static class AuthorRoleExtensions
{
    public static AuthorRole ToAuthorRole(this MessageRole role)
    {
        return role switch
        {
            MessageRole.User => AuthorRole.User,
            MessageRole.Agent => AuthorRole.Assistant,
            _ => throw new ArgumentOutOfRangeException(nameof(role), role, "Invalid message role")
        };
    }

    public static MessageRole ToMessageRole(this AuthorRole role)
    {
        return role.Label switch
        {
            "user" => MessageRole.User,
            "assistant" => MessageRole.Agent,
            _ => throw new ArgumentOutOfRangeException(nameof(role), role, "Invalid author role")
        };
    }
}
