// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Config;

public class ServiceConfig
{
    [Range(0, 65535, ErrorMessage = "Service port out of range.")]
    public int Port { get; set; }

    public bool UseHttp { get; set; }
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string KeyVaultUri { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings
    public string SemanticSkillsDirectory { get; set; } = string.Empty;

    public string AllowedHosts { get; set; } = string.Empty;
    public IEnumerable<string> AllowedOrigins { get; set; } = Array.Empty<string>();

    public void Validate()
    {
        if (this.Port == default)
        {
            throw new ArgumentException(nameof(this.Port), $"{nameof(this.Port)} is not set.");
        }

        if (string.IsNullOrWhiteSpace(this.KeyVaultUri))
        {
            throw new ArgumentException(nameof(this.KeyVaultUri), $"{nameof(this.KeyVaultUri)} is not set.");
        }

        if (string.IsNullOrWhiteSpace(this.SemanticSkillsDirectory))
        {
            throw new ArgumentException(nameof(this.SemanticSkillsDirectory), $"{nameof(this.KeyVaultUri)} is not set.");
        }

        if (string.IsNullOrWhiteSpace(this.AllowedHosts))
        {
            throw new ArgumentException(nameof(this.AllowedHosts), $"{nameof(this.AllowedHosts)} is not set.");
        }
    }
}
