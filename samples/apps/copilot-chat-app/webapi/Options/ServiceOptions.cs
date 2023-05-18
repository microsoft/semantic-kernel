// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration options for the CopilotChat service.
/// </summary>
public class ServiceOptions
{
    public const string PropertyName = "Service";

    /// <summary>
    /// Configuration Key Vault URI
    /// </summary>
    [Url]
    public Uri? KeyVaultUri { get; set; }

    /// <summary>
    /// Local directory in which to load semantic skills.
    /// </summary>
    public string? SemanticSkillsDirectory { get; set; }
}
