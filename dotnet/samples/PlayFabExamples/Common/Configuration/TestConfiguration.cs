// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.Configuration;

namespace PlayFabExamples.Common.Configuration;
public sealed class TestConfiguration
{
    private IConfigurationRoot _configRoot;
    private static TestConfiguration? s_instance;

    private TestConfiguration(IConfigurationRoot configRoot)
    {
        this._configRoot = configRoot;
    }

    public static void Initialize(IConfigurationRoot configRoot)
    {
        s_instance = new TestConfiguration(configRoot);
    }

    public static AzureOpenAIConfig AzureOpenAI => LoadSection<AzureOpenAIConfig>();

    public static BingConfig Bing => LoadSection<BingConfig>();
    public static PlayFabConfig PlayFab => LoadSection<PlayFabConfig>();

    private static T LoadSection<T>([CallerMemberName] string? caller = null)
    {
        if (s_instance == null)
        {
            throw new InvalidOperationException(
                "TestConfiguration must be initialized with a call to Initialize(IConfigurationRoot) before accessing configuration values.");
        }

        if (string.IsNullOrEmpty(caller))
        {
            throw new ArgumentNullException(nameof(caller));
        }
        return s_instance._configRoot.GetSection(caller).Get<T>() ??
            throw new ConfigurationNotFoundException(section: caller);
    }

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.

    public class AzureOpenAIConfig
    {
        public string ServiceId { get; set; }
        public string DeploymentName { get; set; }
        public string ChatDeploymentName { get; set; }
        public string Endpoint { get; set; }
        public string ApiKey { get; set; }
    }

    public class BingConfig
    {
        public string ApiKey { get; set; }
    }

    public class PlayFabConfig
    {
        public string Endpoint { get; set; }
        public string TitleId { get; set; }
        public string TitleSecretKey { get; set; }
        public string SwaggerEndpoint { get; set; }
        public string ReportsCosmosDBEndpoint { get; set; }
        public string ReportsCosmosDBKey { get; set; }
        public string ReportsCosmosDBDatabaseName { get; set; }
        public string ReportsCosmosDBContainerName { get; set; }
    }

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
}
