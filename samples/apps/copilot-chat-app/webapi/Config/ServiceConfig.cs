// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

public class ServiceConfig
{
    public const string PropertyName = "Service";

    public int Port { get; set; } = 40443;

#pragma warning disable CA1056 // URI-like properties should not be strings
    public string KeyVaultUri { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings

    public string SemanticSkillsDirectory { get; set; } = string.Empty;

    public void Validate()
    {
        if (this.Port == default)
        {
            throw new ArgumentException(nameof(this.Port), $"{nameof(this.Port)} is not set.");
        }
    }
}
