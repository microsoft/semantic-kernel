// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.SkillDefinition;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class AIPluginOAuthAttribute : Attribute
{
    public AIPluginManifest.ManifestOAuthAuth Auth { get; }

    /// <summary>
    /// The name of the authentication option.
    /// </summary>
    public string Name
    {
        get => this.Auth.Name;
        private set => this.Auth.Name = value;
    }

    /// <summary>
    /// The description of the authentication option.
    /// </summary>
    public string Description
    {
        get => this.Auth.Description;
        private set => this.Auth.Description = value;
    }

    /// <summary>
    /// The OAuth URL where a user is directed to for the OAuth authentication flow to begin.
    /// </summary>
    public string ClientUrl
    {
        get => this.Auth.ClientUrl.ToString();
        private set => this.Auth.ClientUrl = new Uri(value);
    }

    /// <summary>
    /// The OAuth scopes required to accomplish operations on the user's behalf.
    /// </summary>
    public string Scope
    {
        get => this.Auth.Scope;
        private set => this.Auth.Scope = value;
    }

    /// <summary>
    /// The endpoint used to exchange OAuth code with access token.
    /// </summary>
    public string AuthorizationUrl
    {
        get => this.Auth.AuthorizationUrl.ToString();
        private set => this.Auth.AuthorizationUrl = new Uri(value);
    }

    /// <summary>
    /// When exchanging OAuth code with access token, the expected header 'content-type'.
    /// For example: 'content-type: application/json'
    /// </summary>
    public string AuthorizationContentType
    {
        get => this.Auth.AuthorizationContentType;
        private set => this.Auth.AuthorizationContentType = value;
    }

    /// <summary>
    /// The verification tokens for each service that requires authentication.
    /// </summary>
    public Dictionary<string, string> VerificationTokens
    {
        get => this.Auth.VerificationTokens;
        private set => this.Auth.VerificationTokens = value;
    }

    /// <summary>
    /// Creates an instance of the <see cref="AIPluginOAuthAttribute"/> class.
    /// </summary>
    public AIPluginOAuthAttribute()
    {
        this.Auth = new();
    }
}


