// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Configuration;

namespace Magentic.Services;

internal static class ConfigurationServices
{
    public static IConfigurationRoot ReadSettings()
    {
        Assembly assembly = Assembly.GetExecutingAssembly();

        string rootPath =
            Path.GetDirectoryName(assembly.Location) ??
            Environment.CurrentDirectory;

        IConfigurationRoot configuration = new ConfigurationBuilder()
            .SetBasePath(rootPath)
            .AddEnvironmentVariables()
            .AddUserSecrets(assembly, optional: true)
            .AddJsonFile("settings.json", optional: true, reloadOnChange: true)
            .AddJsonFile("settings.development.json", optional: true, reloadOnChange: true)
            .Build();

        return configuration;
    }
}
