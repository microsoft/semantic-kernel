// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using Newtonsoft.Json;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;

/// <summary>
/// Represents the authentication section for an OpenAI plugin.
/// </summary>
public record OpenAIAuthenticationConfig
{
    /// <summary>
    /// The type of authentication.
    /// </summary>
    [JsonProperty("type")]
    public OpenAIAuthenticationType Type { get; set; } = OpenAIAuthenticationType.None;

    /// <summary>
    /// The type of authorization.
    /// </summary>
    [JsonProperty("authorization_type")]
    public OpenAIAuthorizationType? AuthorizationType { get; set; }

    /// <summary>
    /// The client URL.
    /// </summary>
    [JsonProperty("client_url")]
    public Uri? ClientUrl { get; set; }

    /// <summary>
    /// The authorization URL.
    /// </summary>
    [JsonProperty("authorization_url")]
    public Uri? AuthorizationUrl { get; set; }

    /// <summary>
    /// The authorization content type.
    /// </summary>
    [JsonProperty("authorization_content_type")]
    public OpenAIAuthorizationContentType? AuthorizationContentType { get; set; }

    /// <summary>
    /// The authorization scope.
    /// </summary>
    [JsonProperty("scope")]
    public string? Scope { get; set; }

    /// <summary>
    /// The verification tokens.
    /// </summary>
    [JsonProperty("verification_tokens")]
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

/// <summary>
/// Represents the type of content used for authorization for an OpenAI plugin.
/// </summary>
public enum OpenAIAuthorizationContentType
{
    /// <summary>
    /// JSON content.
    /// </summary>
    [EnumMember(Value = "application/json")]
    JSON,

    /// <summary>
    /// Form URL encoded content.
    /// </summary>
    [EnumMember(Value = "application/x-www-form-urlencoded")]
    FormUrlEncoded
}
