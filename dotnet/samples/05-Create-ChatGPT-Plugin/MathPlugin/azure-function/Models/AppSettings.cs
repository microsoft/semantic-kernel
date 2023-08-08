// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace Models;

#pragma warning disable CA1724
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
public class AppSettings
{
    public const string DefaultConfigFile = "appsettings.json";

    public KernelSettings Kernel { get; set; }
    public AIPluginSettings AIPlugin { get; set; }

    /// <summary>
    /// Load the kernel settings from appsettings.json if the file exists and if not attempt to use user secrets.
    /// </summary>
    public static AppSettings LoadSettings()
    {
        try
        {
            var appSettings = FromFile(DefaultConfigFile);
            appSettings.Kernel.ApiKey = GetApiKey();

            return appSettings;
        }
        catch (InvalidDataException ide)
        {
            Console.Error.WriteLine(
                "Unable to load app settings, please provide configuration settings using instructions in the README.\n" +
                "Please refer to: https://github.com/microsoft/semantic-kernel-starters/blob/main/azure-function/README.md#configuring-the-starter"
            );
            throw new InvalidOperationException(ide.Message);
        }
    }

    /// <summary>
    /// Load the kernel settings from the specified configuration file if it exists.
    /// </summary>
    private static AppSettings FromFile(string configFile = DefaultConfigFile)
    {
        if (!File.Exists(configFile))
        {
            throw new FileNotFoundException($"Configuration not found: {configFile}");
        }

        var configuration = new ConfigurationBuilder()
            .SetBasePath(System.IO.Directory.GetCurrentDirectory())
            .AddJsonFile(configFile, optional: true, reloadOnChange: true)
            .Build();

        return configuration.Get<AppSettings>()
               ?? throw new InvalidDataException($"Invalid app settings in '{configFile}', please provide configuration settings using instructions in the README.");
    }

    /// <summary>
    /// Load the API key for the AI endpoint from user secrets.
    /// </summary>
    internal static string GetApiKey()
    {
        return System.Environment.GetEnvironmentVariable("apiKey", EnvironmentVariableTarget.Process)
               ?? throw new InvalidDataException("Invalid semantic kernel settings in user secrets, please provide configuration settings using instructions in the README.");
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
