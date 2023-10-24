// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

public record OpenAIManifestAuthenticationConfig
{
    public OpenAIAuthenticationType Type { get; set; } = OpenAIAuthenticationType.None;
    public OpenAIAuthorizationType? AuthorizationType { get; set; }
    public string? ClientUrl { get; set; }
    public Uri? AuthorizationUrl { get; set; }
    public string? AuthorizationContentType { get; set; }
    public string? Scope { get; set; }
    public Dictionary<string, string>? VerificationTokens { get; set; }
}

public enum OpenAIAuthenticationType
{
    [EnumMember(Value = "none")]
    None,
    [EnumMember(Value = "user_http")]
    UserHttp,
    [EnumMember(Value = "service_http")]
    ServiceHttp,
    [EnumMember(Value = "oauth")]
    OAuth
}

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OpenAIAuthorizationType
{
    [EnumMember(Value = "basic")]
    Basic,
    [EnumMember(Value = "bearer")]
    Bearer
}
