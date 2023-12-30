#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

internal static class GeminiChatRole
{
    public const string Assistant = "model";
    public const string User = "user";

    public static string FromAuthorRole(AuthorRole role)
    {
        if (role == AuthorRole.Assistant || role == AuthorRole.Tool)
        {
            return "model";
        }

        if (role == AuthorRole.User || role == AuthorRole.System)
        {
            return "user";
        }

        throw new ArgumentException($"Unknown AuthorRole: {role}", nameof(role));
    }

    public static AuthorRole ToAuthorRole(string role) =>
        role switch
        {
            "model" => AuthorRole.Assistant,
            "user" => AuthorRole.User,
            _ => throw new ArgumentException($"Unknown GeminiChatRole: {role}", nameof(role))
        };
}
