// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.Configuration;

public sealed class TestConfiguration2
{
    private readonly IConfigurationRoot _configRoot;
    private static TestConfiguration2? s_instance;

    private TestConfiguration2(IConfigurationRoot configRoot)
    {
        this._configRoot = configRoot;
    }

    public static void Initialize(IConfigurationRoot configRoot)
    {
        s_instance = new TestConfiguration2(configRoot);
    }

    public static OpenAIConfig OpenAI => LoadSection<OpenAIConfig>();
    public static AzureOpenAIConfig AzureOpenAI => LoadSection<AzureOpenAIConfig>();
    public static AzureOpenAIEmbeddingsConfig AzureOpenAIEmbeddings => LoadSection<AzureOpenAIEmbeddingsConfig>();

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
            throw new ArgumentException($"Missing {caller} configuration section");
    }

    public class OpenAIConfig
    {
        public string? ModelId { get; set; }
        public string? ChatModelId { get; set; }
        public string? EmbeddingModelId { get; set; }
        public string? ApiKey { get; set; }
    }

    public class AzureOpenAIConfig
    {
        public string? ServiceId { get; set; }
        public string? DeploymentName { get; set; }
        public string? ModelId { get; set; }
        public string? ChatDeploymentName { get; set; }
        public string? ChatModelId { get; set; }
        public string? ImageDeploymentName { get; set; }
        public string? ImageModelId { get; set; }
        public string? ImageEndpoint { get; set; }
        public string? Endpoint { get; set; }
        public string? ApiKey { get; set; }
        public string? ImageApiKey { get; set; }
    }

    public class AzureOpenAIEmbeddingsConfig
    {
        public string? DeploymentName { get; set; }
        public string? Endpoint { get; set; }
        public string? ApiKey { get; set; }
    }
}
