// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Reliability;
public sealed class ConfigurationNotFoundException : Exception
{
    public string? Section { get; }
    public string? Key { get; }

    public ConfigurationNotFoundException(string section, string key)
        : base($"Configuration key '{section}:{key}' not found")
    {
        this.Section = section;
        this.Key = key;
    }

    public ConfigurationNotFoundException(string section)
    : base($"Configuration section '{section}' not found")
    {
        this.Section = section;
    }

    public ConfigurationNotFoundException() : base()
    {
    }

    public ConfigurationNotFoundException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
