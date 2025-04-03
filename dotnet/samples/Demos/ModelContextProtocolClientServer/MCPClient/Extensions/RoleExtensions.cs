// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.ChatCompletion;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

/// <summary>
/// Extension methods for the <see cref="Role"/> enum.
/// </summary>
internal static class RoleExtensions
{
    /// <summary>
    /// Converts a <see cref="Role"/> to a <see cref="AuthorRole"/>.
    /// </summary>
    /// <param name="role">The MCP role to convert.</param>
    /// <returns>The corresponding <see cref="AuthorRole"/>.</returns>
    public static AuthorRole ToAuthorRole(this Role role)
    {
        return role switch
        {
            Role.User => AuthorRole.User,
            Role.Assistant => AuthorRole.Assistant,
            _ => throw new InvalidOperationException($"Unexpected role '{role}'")
        };
    }
}
