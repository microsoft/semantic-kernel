// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// A chat session
/// </summary>
public class CustomPlugin
{
    /// <summary>
    /// Name of plugin.
    /// </summary>
    [JsonPropertyName("nameForHuman")]
    public string NameForHuman { get; set; } = string.Empty;

    /// <summary>
    /// Name of plugin.
    /// </summary>
    [JsonPropertyName("nameForModel")]
    public string NameForModel { get; set; } = string.Empty;

    /// <summary>
    /// Expected header tag containing auth information.
    /// </summary>
    [JsonPropertyName("authHeaderTag")]
    public string AuthHeaderTag { get; set; } = string.Empty;

    /// <summary>
    /// Auth type, either none or user PAT.
    /// </summary>
    [JsonPropertyName("authType")]
    public string AuthType { get; set; } = string.Empty;

    /// <summary>
    /// Website domain hosting the plugin files.
    /// </summary>
    [JsonPropertyName("manifestDomain")]
    public string ManifestDomain { get; set; } = string.Empty;
}
