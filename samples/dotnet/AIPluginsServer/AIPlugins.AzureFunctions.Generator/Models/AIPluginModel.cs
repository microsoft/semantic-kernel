// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json;

namespace AIPlugins.AzureFunctions.Generator.Models;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
public class AIPluginModel
{
    [JsonProperty("schema_version")]
    public string SchemaVersion { get; set; } = "v1";

    [JsonProperty("name_for_model")]
    public string NameForModel { get; set; }

    [JsonProperty("name_for_human")]
    public string NameForHuman { get; set; }

    [JsonProperty("description_for_model")]
    public string DescriptionForModel { get; set; }

    [JsonProperty("description_for_human")]
    public string DescriptionForHuman { get; set; }

    [JsonProperty("auth")]
    public AuthModel? Auth { get; set; }

    [JsonProperty("api")]
    public ApiModel Api { get; set; }

    [JsonProperty("logo_url")]
    public string? LogoUrl { get; set; }

    [JsonProperty("contact_email")]
    public string ContactEmail { get; set; }

    [JsonProperty("legal_info_url")]
    public string LegalInfoUrl { get; set; }

    public class AuthModel
    {
        [JsonProperty("type")]
        public string Type { get; set; }

        [JsonProperty("authorization_type")]
        public string AuthorizationType { get; set; }
    }

    public class ApiModel
    {
        [JsonProperty("type")]
        public string Type { get; set; } = "openapi";

        [JsonProperty("url")]
        public string Url { get; set; }

        [JsonProperty("has_user_authentication")]
        public bool HasUserAuthentication { get; set; } = false;
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
