// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Represents the authentication section for an OpenAI plugin.
/// </summary>
public record OpenAIAuthenticationManifest
{
    /// <summary>
    /// The type of authentication.
    /// </summary>
    public OpenAIAuthenticationType Type { get; set; } = OpenAIAuthenticationType.None;

    /// <summary>
    /// The type of authorization.
    /// </summary>
    public OpenAIAuthorizationType? AuthorizationType { get; set; }

    /// <summary>
    /// The client URL.
    /// </summary>
    public Uri? ClientUrl { get; set; }

    /// <summary>
    /// The authorization URL.
    /// </summary>
    public Uri? AuthorizationUrl { get; set; }

    /// <summary>
    /// The authorization content type.
    /// </summary>
    public OpenAIAuthorizationContentType? AuthorizationContentType { get; set; }

    /// <summary>
    /// The authorization scope.
    /// </summary>
    public string? Scope { get; set; }

    /// <summary>
    /// The verification tokens.
    /// </summary>
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
