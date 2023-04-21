// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

public class ServiceOptions
{
    public const string PropertyName = "Service";

    public Uri? KeyVaultUri { get; set; }

    public string SemanticSkillsDirectory { get; set; } = string.Empty;
}
