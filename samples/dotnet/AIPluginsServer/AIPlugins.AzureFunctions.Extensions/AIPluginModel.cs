// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace AIPlugins.AzureFunctions.Extensions;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
public class AIPluginModel
{
    [JsonPropertyName("schema_version")]
    public string SchemaVersion { get; set; } = "v1";

    [JsonPropertyName("name_for_model")]
    public string NameForModel { get; set; }

    [JsonPropertyName("name_for_human")]
    public string NameForHuman { get; set; }

    [JsonPropertyName("description_for_model")]
    public string DescriptionForModel { get; set; }

    [JsonPropertyName("description_for_human")]
    public string DescriptionForHuman { get; set; }

    [JsonPropertyName("auth")]
    public AuthModel? Auth { get; set; }

    [JsonPropertyName("api")]
    public ApiModel Api { get; set; }

    [JsonPropertyName("logo_url")]
    public string? LogoUrl { get; set; }

    [JsonPropertyName("contact_email")]
    public string ContactEmail { get; set; }

    [JsonPropertyName("legal_info_url")]
    public string LegalInfoUrl { get; set; }

    public class AuthModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("authorization_type")]
        public string AuthorizationType { get; set; }
    }

    public class ApiModel
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = "openapi";

        [JsonPropertyName("url")]
        public string Url { get; set; }

        [JsonPropertyName("has_user_authentication")]
        public bool HasUserAuthentication { get; set; } = false;
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
