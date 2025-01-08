// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using Azure.AI.Projects;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides an <see cref="AIProjectClient"/> for use by <see cref="AzureAIAgent"/>.
/// </summary>
public sealed class AzureAIClientProvider // $$$ NEEDED ???
{
    /// <summary>
    /// An active client instance.
    /// </summary>
    public AIProjectClient Client { get; }

    /// <summary>
    /// Configuration keys required for <see cref="AgentChannel"/> management.
    /// </summary>
    internal IReadOnlyList<string> ConfigurationKeys { get; }

    private AzureAIClientProvider(AIProjectClient client, IEnumerable<string> keys)
    {
        this.Client = client;
        this.ConfigurationKeys = keys.ToArray();
    }

    /// <summary>
    /// Produce a <see cref="AzureAIClientProvider"/> based on <see cref="AIProjectClient"/>.
    /// </summary>
    /// <param name="connectionString">The service endpoint</param>
    /// <param name="credential">The credentials</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static AzureAIClientProvider ForAzureOpenAI(string connectionString, TokenCredential credential, HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString, nameof(connectionString));
        Verify.NotNull(credential, nameof(credential));

        AIProjectClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new(new AIProjectClient(connectionString, credential, clientOptions), CreateConfigurationKeys(connectionString, httpClient));
    }

    /// <summary>
    /// Directly provide a client instance.
    /// </summary>
    public static AzureAIClientProvider FromClient(AIProjectClient client)
    {
        return new(client, [client.GetType().FullName!, client.GetHashCode().ToString()]);
    }

    private static AIProjectClientOptions CreateAzureClientOptions(HttpClient? httpClient)
    {
        AIProjectClientOptions options = new()
        {
            Diagnostics = { // %%% LOGGING ???
                ApplicationId = HttpHeaderConstant.Values.UserAgent
            },
        };

        ConfigureClientOptions(httpClient, options);

        return options;
    }

    private static void ConfigureClientOptions(HttpClient? httpClient, ClientOptions options)
    {
        //options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AzureAIAgent))), HttpPipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
        }
    }

    private static GenericActionPipelinePolicy CreateRequestHeaderPolicy(string headerName, string headerValue)
    {
        return
            new((message) =>
            {
                if (message?.Request?.Headers.TryGetValue(headerName, out string? _) == false)
                {
                    message.Request.Headers.Add(headerName, headerValue);
                }
            });
    }

    private static IEnumerable<string> CreateConfigurationKeys(string connectionString, HttpClient? httpClient)
    {
        yield return connectionString;

        if (httpClient is not null)
        {
            if (httpClient.BaseAddress is not null)
            {
                yield return httpClient.BaseAddress.AbsoluteUri;
            }

            foreach (string header in httpClient.DefaultRequestHeaders.SelectMany(h => h.Value))
            {
                yield return header;
            }
        }
    }
}
