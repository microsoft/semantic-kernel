// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using static Microsoft.SemanticKernel.SkillDefinition.AIPluginManifest;

namespace Microsoft.SemanticKernel.SkillDefinition;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class AIPluginServiceHttpAuthAttribute : Attribute
{
    public ManifestServiceHttpAuth Auth { get; }

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
    /// The type of HTTP authorization header.
    /// </summary>
    public HttpAuthorizationType AuthorizationType => this.Auth.AuthorizationType;

    /// <summary>
    /// The verification tokens for each service that requires authentication.
    /// </summary>
    public Dictionary<string, string> VerificationTokens
    {
        get { return this.Auth.VerificationTokens; }
        set { this.Auth.VerificationTokens = value; }
    }

    public AIPluginServiceHttpAuthAttribute(HttpAuthorizationType authorizationType)
    {
        this.Auth = new(authorizationType);
    }
}
