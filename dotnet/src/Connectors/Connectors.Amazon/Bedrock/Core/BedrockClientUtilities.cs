// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Net;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Bedrock.Core;

/// <summary>
/// Utility functions for the Bedrock clients.
/// </summary>
public class BedrockClientUtilities
{
    /// <summary>
    /// Convert the Http Status Code in Converse Response to the Activity Status Code for Semantic Kernel activity.
    /// </summary>
    /// <param name="httpStatusCode"></param>
    /// <returns></returns>
    public ActivityStatusCode ConvertHttpStatusCodeToActivityStatusCode(HttpStatusCode httpStatusCode)
    {
        if ((int)httpStatusCode >= 200 && (int)httpStatusCode < 300)
        {
            // 2xx status codes represent success
            return ActivityStatusCode.Ok;
        }
        else if ((int)httpStatusCode >= 400 && (int)httpStatusCode < 600)
        {
            // 4xx and 5xx status codes represent errors
            return ActivityStatusCode.Error;
        }
        else
        {
            // Any other status code is considered unset
            return ActivityStatusCode.Unset;
        }
    }
    /// <summary>
    /// Map Conversation role (value) to author role to build message content for semantic kernel output.
    /// </summary>
    /// <param name="role"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    public AuthorRole MapConversationRoleToAuthorRole(string role)
    {
        return role switch
        {
            "user" => AuthorRole.User,
            "assistant" => AuthorRole.Assistant,
            "system" => AuthorRole.System,
            _ => throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}")
        };
    }
}
