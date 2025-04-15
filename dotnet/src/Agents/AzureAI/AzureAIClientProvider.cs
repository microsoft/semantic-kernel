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
public sealed class AzureAIClientProvider
{
    private AgentsClient? _agentsClient;

    /// <summary>
    /// Gets an active client instance.
    /// </summary>
    public AIProjectClient Client { get; }

    /// <summary>
    /// Gets an active assistant client instance.
    /// </summary>
    public AgentsClient AgentsClient => this._agentsClient ??= this.Client.GetAgentsClient();

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
    /// Produces a <see cref="AzureAIClientProvider"/>.
    /// </summary>
    /// <param name="connectionString">The Azure AI Foundry project connection string, in the form `endpoint;subscription_id;resource_group_name;project_name`.</param>
    /// <param name="credential"> A credential used to authenticate to an Azure Service.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static AzureAIClientProvider FromConnectionString(
        string connectionString,
        TokenCredential credential,
        HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString, nameof(connectionString));
        Verify.NotNull(credential, nameof(credential));

        AIProjectClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new(new AIProjectClient(connectionString, credential, clientOptions), CreateConfigurationKeys(connectionString, httpClient));
    }

    /// <summary>
    /// Provides a client instance directly.
    /// </summary>
    public static AzureAIClientProvider FromClient(AIProjectClient client)
    {
        return new(client, [client.GetType().FullName!, client.GetHashCode().ToString()]);
    }

    internal static AIProjectClientOptions CreateAzureClientOptions(HttpClient? httpClient)
    {
        AIProjectClientOptions options =
            new()
            {
                Diagnostics = {
                    ApplicationId = HttpHeaderConstant.Values.UserAgent,
                }
            };

        options.AddPolicy(new SemanticKernelHeadersPolicy(), HttpPipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            // Disable retry policy if and only if a custom HttpClient is provided.
            options.RetryPolicy = new RetryPolicy(maxRetries: 0);
        }

        return options;
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

    private class SemanticKernelHeadersPolicy : HttpPipelineSynchronousPolicy
    {
        public override void OnSendingRequest(HttpMessage message)
        {
            message.Request.Headers.Add(
                HttpHeaderConstant.Names.SemanticKernelVersion,
                HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AzureAIAgent)));
        }
    }
}
