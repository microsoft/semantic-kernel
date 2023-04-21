// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for the CopilotChat service.
/// </summary>
public class ServiceOptions
{
    public const string PropertyName = "Service";

    /// <summary>
    /// Configuration Keyvault URI
    /// </summary>
    public Uri? KeyVaultUri { get; set; }

    /// <summary>
    /// Local directory in which to load semantic skills.
    /// </summary>
    public string SemanticSkillsDirectory { get; set; } = string.Empty;
}
