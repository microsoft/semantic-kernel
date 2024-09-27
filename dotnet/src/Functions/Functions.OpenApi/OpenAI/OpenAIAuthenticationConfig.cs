// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents the authentication section for an OpenAI plugin.
/// </summary>
public class OpenAIAuthenticationConfig
{
    /// <summary>
    /// The type of authentication.
    /// </summary>
    [JsonPropertyName("type")]
    public OpenAIAuthenticationType Type { get; set; } = OpenAIAuthenticationType.None;

    /// <summary>
    /// The type of authorization.
    /// </summary>
    [JsonPropertyName("authorization_type")]
    public OpenAIAuthorizationType AuthorizationType { get; set; }

    /// <summary>
    /// The client URL.
    /// </summary>
    [JsonPropertyName("client_url")]
    public Uri? ClientUrl { get; set; }

    /// <summary>
    /// The authorization URL.
    /// </summary>
    [JsonPropertyName("authorization_url")]
    public Uri? AuthorizationUrl { get; set; }

    /// <summary>
    /// The authorization content type.
    /// </summary>
    [JsonPropertyName("authorization_content_type")]
    public string? AuthorizationContentType { get; set; }

    /// <summary>
    /// The authorization scope.
    /// </summary>
    [JsonPropertyName("scope")]
    public string? Scope { get; set; }

    /// <summary>
    /// The verification tokens.
    /// </summary>
    [JsonPropertyName("verification_tokens")]
    public Dictionary<string, string>? VerificationTokens { get; set; }
}

/// <summary>
/// Represents the type of authentication for an OpenAI plugin.
/// </summary>
public enum OpenAIAuthenticationType
{
    /// <summary>
    /// No authentication.
    /// </summary>
    None,

    /// <summary>
    /// User HTTP authentication.
    /// </summary>
    UserHttp,

    /// <summary>
    /// Service HTTP authentication.
    /// </summary>
    ServiceHttp,

    /// <summary>
    /// OAuth authentication.
    /// </summary>
    OAuth
}

/// <summary>
/// Represents the type of authorization for an OpenAI plugin.
/// </summary>
public enum OpenAIAuthorizationType
{
    /// <summary>
    /// Basic authorization.
    /// </summary>
    Basic,

    /// <summary>
    /// Bearer authorization.
    /// </summary>
    Bearer
}
