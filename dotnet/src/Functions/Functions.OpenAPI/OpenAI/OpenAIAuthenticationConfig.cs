// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;

/// <summary>
/// Represents the authentication section for an OpenAI plugin.
/// </summary>
public record OpenAIAuthenticationConfig
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
    public OpenAIAuthorizationType? AuthorizationType { get; set; }

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
    public OpenAIAuthorizationContentType? AuthorizationContentType { get; set; }

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
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OpenAIAuthenticationType
{
    /// <summary>
    /// No authentication.
    /// </summary>
    [EnumMember(Value = "none")]
    None,

    /// <summary>
    /// User HTTP authentication.
    /// </summary>
    [EnumMember(Value = "user_http")]
    UserHttp,

    /// <summary>
    /// Service HTTP authentication.
    /// </summary>
    [EnumMember(Value = "service_http")]
    ServiceHttp,

    /// <summary>
    /// OAuth authentication.
    /// </summary>
    [EnumMember(Value = "oauth")]
    OAuth
}

/// <summary>
/// Represents the type of authorization for an OpenAI plugin.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OpenAIAuthorizationType
{
    /// <summary>
    /// Basic authorization.
    /// </summary>
    [EnumMember(Value = "Basic")]
    Basic,

    /// <summary>
    /// Bearer authorization.
    /// </summary>
    [EnumMember(Value = "Bearer")]
    Bearer
}

/// <summary>
/// Represents the type of content used for authorization for an OpenAI plugin.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
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
