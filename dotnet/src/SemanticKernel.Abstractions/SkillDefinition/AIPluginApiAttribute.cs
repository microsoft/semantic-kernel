// Copyright (c) Microsoft. All rights reserved.

using System;
using static Microsoft.SemanticKernel.SkillDefinition.AIPluginManifest;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// An attribute that specifies the API model for an AI plugin class.
/// </summary>
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class AIPluginApiAttribute : Attribute
{
    /// <summary>
    /// Gets the API model for the AI plugin class.
    /// </summary>
    public ApiModel ApiModel { get; }

    /// <summary>
    /// Gets or sets the url of the API.
    /// </summary>
    public string Url
    {
        get => this.ApiModel.Url.ToString();
        private set => this.ApiModel.Url = new Uri(value);
    }

    /// <summary>
    /// Gets or sets the type of the API. Currently only "openapi".
    /// </summary>
    public string Type
    {
        get => this.ApiModel.Type;
        private set => this.ApiModel.Type = value;
    }

    /// <summary>
    /// Gets or sets a value indicating whether the AI plugin requires user authentication.
    /// </summary>
    public bool IsUserAuthenticated
    {
        get => this.ApiModel.IsUserAuthenticated;
        private set => this.ApiModel.IsUserAuthenticated = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AIPluginApiAttribute"/> class with the specified URL, type, and authentication flag.
    /// </summary>
    /// <param name="url">The URL of the AI plugin API endpoint.</param>
    /// <param name="type">The type of the AI plugin, such as "text" or "image".</param>
    /// <param name="isUserAuthenticated">A value indicating whether the AI plugin requires user authentication.</param>
    public AIPluginApiAttribute(string url, string type = "openapi", bool isUserAuthenticated = false)
    {
        this.ApiModel = new(new Uri(url));
        this.Type = type;
        this.IsUserAuthenticated = isUserAuthenticated;
    }
}
