// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace skchatgptazurefunction.PluginShared;

/// <summary>
/// This class represents the OpenAI plugin authentication schema.
/// </summary>
public class PluginAuth
{
    /// <summary>
    /// Tokens for API key authentication
    /// </summary>
    public class VerificationTokens
    {
        /// <summary>
        /// The API key
        /// </summary>
        public string OpenAI { get; set; } = string.Empty;
    }

    /// <summary>
    /// The authentication schema
    /// Supported values: none, service_http, user_http
    /// </summary>
    public string Type { get; set; } = "none";

    /// <summary>
    /// Manifest schema version
    /// </summary>
    [JsonPropertyName("authorization_type")]
    public string AuthorizationType { get; } = "bearer";

    /// <summary>
    /// Tokens for API key authentication
    /// </summary>
    [JsonPropertyName("verification_tokens")]
    public VerificationTokens Tokens { get; set; } = new VerificationTokens();
}
