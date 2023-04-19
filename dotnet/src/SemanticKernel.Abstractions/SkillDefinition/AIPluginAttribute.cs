// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

[AttributeUsage(AttributeTargets.Class, AllowMultiple = false)]
public sealed class AIPluginAttribute : Attribute
{
    public AIPluginManifest AIPluginManifest { get; } = new();

    /// <summary>
    /// Name the model will used to target the plugin
    /// </summary>
    public string NameForModel
    {
        get => this.AIPluginManifest.NameForModel;
        private set => this.AIPluginManifest.NameForModel = value;
    }

    /// <summary>
    /// Human-readable name, such as the full company name
    /// </summary>
    public string NameForHuman
    {
        get => this.AIPluginManifest.NameForHuman;
        private set => this.AIPluginManifest.NameForHuman = value;
    }

    /// <summary>
    /// Description better tailored to the model, such as token context length considerations or
    /// keyword usage for improved plugin prompting.
    /// </summary>
    public string DescriptionForModel
    {
        get => this.AIPluginManifest.DescriptionForModel;
        private set => this.AIPluginManifest.DescriptionForModel = value;
    }

    /// <summary>
    /// Human-readable description of the plugin
    /// </summary>
    public string DescriptionForHuman
    {
        get => this.AIPluginManifest.DescriptionForHuman;
        private set => this.AIPluginManifest.DescriptionForHuman = value;
    }

    /// <summary>
    /// Manifest schema version
    /// </summary>
    public string SchemaVersion
    {
        get => this.AIPluginManifest.SchemaVersion;
        private set => this.AIPluginManifest.SchemaVersion = value;
    }

    /// <summary>
    /// URL used to fetch the plugin's logo
    /// </summary>
    public string LogoUrl
    {
        get => this.AIPluginManifest.LogoUrl.ToString();
        set => this.AIPluginManifest.LogoUrl = new Uri(value);
    }

    /// <summary>
    /// Email contact for safety/moderation reachout, support, and deactivation
    /// </summary>
    public string ContactEmail
    {
        get => this.AIPluginManifest.ContactEmail;
        set => this.AIPluginManifest.ContactEmail = value;
    }

    /// <summary>
    /// Redirect URL for users to view plugin information
    /// </summary>
    public string LegalInfoUrl
    {
        get => this.AIPluginManifest.LegalInfoUrl.ToString();
        set => this.AIPluginManifest.LegalInfoUrl = new Uri(value);
    }

    /// <summary>
    /// Creates an instance of the <see cref="AIPluginAttribute"/> class.
    /// </summary>
    /// <param name="nameForModel">Name the model will used to target the plugin.</param>
    /// <param name="nameForHuman">Human-readable name, such as the full company name.</param>
    /// <param name="descriptionForModel">Description better tailored to the model, such as token context length considerations or
    /// keyword usage for improved plugin prompting.</param>
    /// <param name="descriptionForHuman">Description better tailored to the model, such as token context length considerations or
    /// keyword usage for improved plugin prompting.</param>
    public AIPluginAttribute(string nameForModel, string nameForHuman, string descriptionForModel, string descriptionForHuman)
    {
        this.NameForModel = nameForModel;
        this.NameForHuman = nameForHuman;
        this.DescriptionForModel = descriptionForModel;
        this.DescriptionForHuman = descriptionForHuman;
    }

    /// <summary>
    /// Creates an instance of the <see cref="AIPluginAttribute"/> class.
    /// </summary>
    /// <param name="name">Name, applies to both <see cref="NameForModel"/> and <see cref="NameForHuman"/> properties.</param>
    /// <param name="description">Description, applies to both <see cref="DescriptionForModel"/> and <see cref="DescriptionForHuman"/> properties.</param>
    [SuppressMessage("Design", "CA1019:Define accessors for attribute arguments", Justification = "Args populate other public accessors")]
    public AIPluginAttribute(string name, string description)
        : this(name, name, description, description)
    {
    }
}
