// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.Configuration;

namespace Configuration;

public sealed class TestConfiguration
{
    private readonly IConfigurationRoot _configRoot;
    private static TestConfiguration? s_instance;

    private TestConfiguration(IConfigurationRoot configRoot)
    {
        this._configRoot = configRoot;
    }

    public static void Initialize(IConfigurationRoot configRoot)
    {
        s_instance = new TestConfiguration(configRoot);
    }

    public static OpenAIConfig OpenAI => LoadSection<OpenAIConfig>();
    public static AzureOpenAIConfig AzureOpenAI => LoadSection<AzureOpenAIConfig>();

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
            throw new ConfigurationException(section: caller);
    }

    public class OpenAIConfig
    {
        public string ModelId { get; set; } = string.Empty;
        public string ChatModelId { get; set; } = string.Empty;
        public string EmbeddingModelId { get; set; } = string.Empty;
        public string ApiKey { get; set; } = string.Empty;
    }

    public class AzureOpenAIConfig
    {
        public string ServiceId { get; set; } = string.Empty;
        public string DeploymentName { get; set; } = string.Empty;
        public string ChatDeploymentName { get; set; } = string.Empty;
        public string Endpoint { get; set; } = string.Empty;
        public string ApiKey { get; set; } = string.Empty;
    }
}
