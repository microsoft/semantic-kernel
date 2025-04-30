// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.Configuration;

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

    public static AzureOpenAIConfig? AzureOpenAI => LoadSection<AzureOpenAIConfig>();

    public static AzureAIInferenceConfig? AzureAIInference => LoadSection<AzureAIInferenceConfig>();

    public static ApplicationInsightsConfig ApplicationInsights => LoadRequiredSection<ApplicationInsightsConfig>();

    public static GoogleAIConfig? GoogleAI => LoadSection<GoogleAIConfig>();

    public static HuggingFaceConfig? HuggingFace => LoadSection<HuggingFaceConfig>();

    public static MistralAIConfig? MistralAI => LoadSection<MistralAIConfig>();

    private static T? LoadSection<T>([CallerMemberName] string? caller = null)
    {
        if (s_instance is null)
        {
            throw new InvalidOperationException(
                "TestConfiguration must be initialized with a call to Initialize(IConfigurationRoot) before accessing configuration values.");
        }

        if (string.IsNullOrEmpty(caller))
        {
            throw new ArgumentNullException(nameof(caller));
        }

        return s_instance._configRoot.GetSection(caller).Get<T>();
    }

    private static T LoadRequiredSection<T>([CallerMemberName] string? caller = null)
    {
        var section = LoadSection<T>(caller);
        if (section is not null)
        {
            return section;
        }

        throw new KeyNotFoundException($"Could not find configuration section {caller}");
    }

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
    public class AzureOpenAIConfig
    {
        public string ChatDeploymentName { get; set; }
        public string ChatModelId { get; set; }
        public string Endpoint { get; set; }
        public string ApiKey { get; set; }
    }

    public class ApplicationInsightsConfig
    {
        public string ConnectionString { get; set; }
    }

    public class GoogleAIConfig
    {
        public string ApiKey { get; set; }
        public string EmbeddingModelId { get; set; }
        public GeminiConfig Gemini { get; set; }

        public class GeminiConfig
        {
            public string ModelId { get; set; }
        }
    }

    public class HuggingFaceConfig
    {
        public string ApiKey { get; set; }
        public string ModelId { get; set; }
        public string EmbeddingModelId { get; set; }
    }

    public class MistralAIConfig
    {
        public string ApiKey { get; set; }
        public string ChatModelId { get; set; }
    }

    public class AzureAIInferenceConfig
    {
        public Uri Endpoint { get; set; }
        public string ApiKey { get; set; }
        public string ModelId { get; set; }
    }

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
}
