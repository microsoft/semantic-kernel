// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Reflection;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.

public class AIPluginManifest
{
    public static AIPluginManifest? GetAIPluginManifest<TClass>()
    {
        return GetAIPluginManifest(typeof(TClass));
    }

    public static AIPluginManifest? GetAIPluginManifest(Type classType)
    {
        var classInfo = classType.GetTypeInfo();
        if (!classInfo.IsClass) { return null; }

        // First check for an AIPluginAttribute on the class;
        AIPluginManifest? pluginManifest = classInfo.GetCustomAttribute<AIPluginAttribute>()?.AIPluginManifest;
        if (pluginManifest == null) { return null; }

        pluginManifest.Api = classInfo.GetCustomAttribute<AIPluginApiAttribute>()?.ApiModel
            ?? throw new MissingFieldException("When specifying AIPluginAttribute on a class, the AIPluginApiModelAttribute is also required.");

        pluginManifest.Auth = classInfo.GetCustomAttribute<AIPluginOAuthAttribute>()?.Auth
            ?? classInfo.GetCustomAttribute<AIPluginUserHttpAuthAttribute>()?.Auth
            ?? classInfo.GetCustomAttribute<AIPluginServiceHttpAuthAttribute>()?.Auth
            ?? AIPluginManifest.ManifestAuth.None;

        return pluginManifest;
    }

    /// <summary>
    /// Manifest schema version
    /// </summary>
    [Required]
    [JsonPropertyName("schema_version")]
    public string SchemaVersion { get; set; } = "v1";

    /// <summary>
    /// Name the model will used to target the plugin
    /// </summary>
    [Required]
    [MaxLength(50)]
    [JsonPropertyName("name_for_model")]
    public string NameForModel { get; set; } = "";

    /// <summary>
    /// Human-readable name, such as the full company name
    /// </summary>
    [Required]
    [MaxLength(50)]
    [JsonPropertyName("name_for_human")]
    public string NameForHuman { get; set; } = "";

    /// <summary>
    /// Description better tailored to the model, such as token context length considerations or
    /// keyword usage for improved plugin prompting.
    /// </summary>
    [Required]
    [MaxLength(8000)]
    [JsonPropertyName("description_for_model")]
    public string DescriptionForModel { get; set; } = "";

    /// <summary>
    /// Human-readable description of the plugin
    /// </summary>
    [Required]
    [MaxLength(120)]
    [JsonPropertyName("description_for_human")]
    public string DescriptionForHuman { get; set; } = "";

    /// <summary>
    /// Email contact for safety/moderation reachout, support, and deactivation
    /// </summary>
    [Required]
    [JsonPropertyName("contact_email")]
    public string ContactEmail { get; set; } = "";

    /// <summary>
    /// URL used to fetch the plugin's logo
    /// </summary>
    [Required]
    [JsonPropertyName("logo_url")]
    public Uri LogoUrl { get; set; } = new Uri("");

    /// <summary>
    /// Redirect URL for users to view plugin information
    /// </summary>
    [Required]
    [JsonPropertyName("legal_info_url")]
    public Uri LegalInfoUrl { get; set; } = new Uri("");

    /// <summary>
    /// Authentication schema
    /// </summary>
    [Required]
    [JsonPropertyName("auth")]
    public ManifestAuth Auth { get; set; } = ManifestAuth.None;

    /// <summary>
    /// API specification
    /// </summary>
    [Required]
    [JsonPropertyName("api")]
    public ApiModel Api { get; set; } = ApiModel.None;

    #region inner-classes

    public class ApiModel
    {
        public static readonly ApiModel None = new ApiModel(new Uri(string.Empty));

        public ApiModel(Uri url)
        {
            this.Url = url;
        }

        [JsonPropertyName("type")]
        public string Type { get; set; } = "openapi";

        [JsonPropertyName("url")]
        public Uri Url { get; set; }

        [JsonPropertyName("is_user_authenticated")]
        public bool IsUserAuthenticated { get; set; } = false;
    }

    /// <summary>
    /// Represents the base type for manifest authentication options.
    /// </summary>
    public class ManifestAuth
    {
        public static readonly ManifestAuth None = new(ManifestAuthType.None);

        protected ManifestAuth(ManifestAuthType authType)
        {
            this.AuthType = authType;
        }

        /// <summary>
        /// The type of authentication.
        /// </summary>
        [JsonIgnore]
        public ManifestAuthType AuthType { get; protected set; }

        [JsonPropertyName("type")]
        public string AuthTypeString => this.AuthType.ToString();

        /// <summary>
        /// The name of the authentication option.
        /// </summary>
        [JsonPropertyName("name")]
        public string Name { get; set; }

        /// <summary>
        /// The description of the authentication option.
        /// </summary>
        [JsonPropertyName("description")]
        public string Description { get; set; }
    }

    /// <summary>
    /// Represents the app-level API keys authentication option.
    /// </summary>
    public class ManifestServiceHttpAuth : ManifestAuth
    {
        public ManifestServiceHttpAuth()
            : base(ManifestAuthType.ServiceHttp)
        {
        }

        public ManifestServiceHttpAuth(HttpAuthorizationType authType)
            : this()
        {
            this.AuthorizationType = authType;
        }

        /// <summary>
        /// The type of HTTP authorization header.
        /// </summary>
        [JsonPropertyName("authorization_type")]
        public HttpAuthorizationType AuthorizationType { get; set; }

        /// <summary>
        /// The verification tokens for each service that requires authentication.
        /// </summary>
        [JsonPropertyName("verification_tokens")]
        public Dictionary<string, string> VerificationTokens { get; set; } = new();
    }

    /// <summary>
    /// Represents the user-level HTTP authentication option.
    /// </summary>
    public class ManifestUserHttpAuth : ManifestAuth
    {
        public ManifestUserHttpAuth()
            : base(ManifestAuthType.UserHttp)
        {
        }

        public ManifestUserHttpAuth(HttpAuthorizationType authType)
            : this()
        {
            this.AuthorizationType = authType;
        }

        /// <summary>
        /// The type of HTTP authorization header.
        /// </summary>
        [JsonPropertyName("authorization_type")]
        public HttpAuthorizationType AuthorizationType { get; set; }
    }

    /// <summary>
    /// Represents the OAuth authentication option.
    /// </summary>
    public class ManifestOAuthAuth : ManifestAuth
    {
        public ManifestOAuthAuth()
            : base(ManifestAuthType.OAuth)
        {
        }

        /// <summary>
        /// The OAuth URL where a user is directed to for the OAuth authentication flow to begin.
        /// </summary>
        [JsonPropertyName("client_url")]
        public Uri ClientUrl { get; set; }

        /// <summary>
        /// The OAuth scopes required to accomplish operations on the user's behalf.
        /// </summary>
        [JsonPropertyName("scope")]
        public string Scope { get; set; }

        /// <summary>
        /// The endpoint used to exchange OAuth code with access token.
        /// </summary>
        [JsonPropertyName("authorization_url")]
        public Uri AuthorizationUrl { get; set; }

        /// <summary>
        /// When exchanging OAuth code with access token, the expected header 'content-type'.
        /// For example: 'content-type: application/json'
        /// </summary>
        [JsonPropertyName("authorization_content_type")]
        public string AuthorizationContentType { get; set; }

        /// <summary>
        /// The verification tokens for each service that requires authentication.
        /// </summary>
        [JsonPropertyName("verification_tokens")]
        public Dictionary<string, string> VerificationTokens { get; set; }
    }

    /// <summary>
    /// Represents the type of HTTP authorization header.
    /// </summary>
    public class HttpAuthorizationType
    {
        private string _scheme;

        /// <summary>
        /// The authorization header uses the basic scheme.
        /// </summary>
        public static readonly HttpAuthorizationType Basic = new("basic");

        /// <summary>
        /// The authorization header uses the bearer scheme.
        /// </summary>
        ///
        public static readonly HttpAuthorizationType Bearer = new("bearer");

        public HttpAuthorizationType(string scheme)
        {
            this._scheme = scheme;
        }

        public override string ToString()
        {
            return this._scheme;
        }
    }

    public class ManifestAuthType
    {
        private string _authTypeName;

        /// <summary>
        /// No authentication required.
        /// </summary>
        public static readonly ManifestAuthType None = new("none");

        /// <summary>
        /// User-level HTTP authentication.
        /// </summary>
        public static readonly ManifestAuthType UserHttp = new("user_http");

        /// <summary>
        /// App-level API keys authentication.
        /// </summary>
        public static readonly ManifestAuthType ServiceHttp = new("service_http");

        /// <summary>
        /// OAuth authentication.
        /// </summary>
        public static readonly ManifestAuthType OAuth = new("oauth");

        public ManifestAuthType(string authTypeName)
        {
            this._authTypeName = authTypeName;
        }

        public override string ToString()
        {
            return this._authTypeName;
        }
    }
    #endregion inner-classes
}

#pragma warning restore CS8618
