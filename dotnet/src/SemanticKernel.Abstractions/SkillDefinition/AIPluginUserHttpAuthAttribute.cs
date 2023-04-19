// Copyright (c) Microsoft. All rights reserved.

using System;
using static Microsoft.SemanticKernel.SkillDefinition.AIPluginManifest;

namespace Microsoft.SemanticKernel.SkillDefinition;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class AIPluginUserHttpAuthAttribute : Attribute
{
    public ManifestUserHttpAuth Auth { get; }

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

    public AIPluginUserHttpAuthAttribute(HttpAuthorizationType authorizationType)
    {
        this.Auth = new ManifestUserHttpAuth(authorizationType);
    }
}


