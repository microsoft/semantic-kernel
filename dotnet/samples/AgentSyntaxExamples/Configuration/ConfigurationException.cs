// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Configuration;

public sealed class ConfigurationException : Exception
{
    public string? Section { get; }
    public string? Key { get; }

    public ConfigurationException(string section, string key)
        : base($"Configuration key '{section}:{key}' not found")
    {
        this.Section = section;
        this.Key = key;
    }

    public ConfigurationException(string section)
    : base($"Configuration section '{section}' not found")
    {
        this.Section = section;
    }

    public ConfigurationException() : base()
    {
    }

    public ConfigurationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
