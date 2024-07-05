// Copyright (c) Microsoft. All rights reserved.
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Threading;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

internal static class OpenAIClientFactory
{
    /// <summary>
    /// Avoids an exception from OpenAI Client when a custom endpoint is provided without an API key.
    /// </summary>
    private const string SingleSpaceKey = " ";

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="config"></param>
    /// <returns></returns>
    public static OpenAIClient CreateClient(OpenAIConfiguration config)
    {
        OpenAIClient client;

        // Inspect options
        switch (config.Type)
        {
            case OpenAIConfiguration.OpenAIConfigurationType.AzureOpenAIKey:
            {
                AzureOpenAIClientOptions clientOptions = CreateAzureClientOptions(config);
                client = new AzureOpenAIClient(config.Endpoint, config.ApiKey!, clientOptions);
                break;
            }
            case OpenAIConfiguration.OpenAIConfigurationType.AzureOpenAICredential:
            {
                AzureOpenAIClientOptions clientOptions = CreateAzureClientOptions(config);
                client = new AzureOpenAIClient(config.Endpoint, config.Credentials!, clientOptions);
                break;
            }
            case OpenAIConfiguration.OpenAIConfigurationType.OpenAI:
            {
                OpenAIClientOptions clientOptions = CreateOpenAIClientOptions(config);
                client = new OpenAIClient(config.ApiKey ?? SingleSpaceKey, clientOptions);
                break;
            }
            default:
                throw new KernelException($"Unsupported configuration type: {config.Type}");
        }

        return client;
    }

    private static AzureOpenAIClientOptions CreateAzureClientOptions(OpenAIConfiguration config)
    {
        AzureOpenAIClientOptions options =
            new()
            {
                ApplicationId = HttpHeaderConstant.Values.UserAgent,
                Endpoint = config.Endpoint,
            };

        ConfigureClientOptions(config.HttpClient, options);

        return options;
    }

    private static OpenAIClientOptions CreateOpenAIClientOptions(OpenAIConfiguration config)
    {
        OpenAIClientOptions options =
            new()
            {
                ApplicationId = HttpHeaderConstant.Values.UserAgent,
                Endpoint = config.Endpoint ?? config.HttpClient?.BaseAddress,
            };

        if (!string.IsNullOrWhiteSpace(config.OrganizationId))
        {
            options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.OpenAIOrganizationId, config.OrganizationId!), PipelinePosition.PerCall);
        }

        ConfigureClientOptions(config.HttpClient, options);

        return options;
    }

    private static void ConfigureClientOptions(HttpClient? httpClient, OpenAIClientOptions options)
    {
        options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIAssistantAgent))), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable default timeout
        }
    }

    private static GenericActionPipelinePolicy CreateRequestHeaderPolicy(string headerName, string headerValue)
        =>
            new((message) =>
                {
                    if (message?.Request?.Headers?.TryGetValue(headerName, out string? _) == false)
                    {
                        message.Request.Headers.Set(headerName, headerValue);
                    }
                });
}
