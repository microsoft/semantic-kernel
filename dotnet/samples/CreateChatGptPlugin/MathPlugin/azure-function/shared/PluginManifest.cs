// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace skchatgptazurefunction.PluginShared;

/// <summary>
/// This class represents the OpenAI plugin manifest:
/// https://platform.openai.com/docs/plugins/getting-started/plugin-manifest
/// </summary>
public class PluginManifest
{
    /// <summary>
    /// Manifest schema version
    /// </summary>
    [JsonPropertyName("schema_version")]
    public string SchemaVersion { get; set; } = "v1";

    /// <summary>
    /// The name of the plugin that the model will use
    /// </summary>
    [JsonPropertyName("name_for_model")]
    public string NameForModel { get; set; } = string.Empty;

    /// <summary>
    /// Human-readable name of the plugin
    /// </summary>
    [JsonPropertyName("name_for_human")]
    public string NameForHuman { get; set; } = string.Empty;

    /// <summary>
    /// Description of the plugin that the model will use
    /// </summary>
    [JsonPropertyName("description_for_model")]
    public string DescriptionForModel { get; set; } = string.Empty;

    /// <summary>
    /// Human-readable description of the plugin
    /// </summary>
    [JsonPropertyName("description_for_human")]
    public string DescriptionForHuman { get; set; } = string.Empty;

    /// <summary>
    /// The authentication schema
    /// </summary>
    public PluginAuth Auth { get; set; } = new PluginAuth();

    /// <summary>
    /// The API specification
    /// </summary>
    public PluginApi Api { get; set; } = new PluginApi();

#pragma warning disable CA1056 // URI-like properties should not be strings
    /// <summary>
    /// Redirect URL for users to get more information about the plugin
    /// </summary>
    [JsonPropertyName("legal_info_url")]
    public string LegalInfoUrl { get; set; } = string.Empty;

    /// <summary>
    /// URL used to fetch the logo
    /// </summary>
    [JsonPropertyName("logo_url")]
    public string LogoUrl { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// Email contact for safety/moderation, support and deactivation
    /// </summary>
    [JsonPropertyName("contact_email")]
    public string ContactEmail { get; set; } = string.Empty;

    /// <summary>
    /// "Bearer" or "Basic"
    /// </summary>
    public string HttpAuthorizationType { get; set; } = string.Empty;
}
