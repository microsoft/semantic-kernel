// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;
using Azure.AI.Agents.Persistent;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides an <see cref="PersistentAgentsClient"/> for use by <see cref="AzureAIAgent"/>.
/// </summary>
public sealed partial class AzureAIAgent : Agent
{
    /// <summary>
    /// Produces a <see cref="PersistentAgentsClient"/>.
    /// </summary>
    /// <param name="endpoint">The Azure AI Foundry project endpoint.</param>
    /// <param name="credential"> A credential used to authenticate to an Azure Service.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static PersistentAgentsClient CreateAgentsClient(
        string endpoint,
        TokenCredential credential,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(endpoint, nameof(endpoint));
        Verify.NotNull(credential, nameof(credential));

        PersistentAgentsAdministrationClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new PersistentAgentsClient(endpoint, credential, clientOptions);
    }

    private static PersistentAgentsAdministrationClientOptions CreateAzureClientOptions(HttpClient? httpClient)
    {
        PersistentAgentsAdministrationClientOptions options = new();

        options.AddPolicy(new SemanticKernelHeadersPolicy(), HttpPipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            // Disable retry policy if and only if a custom HttpClient is provided.
            options.RetryPolicy = new RetryPolicy(maxRetries: 0);
        }

        return options;
    }

    private class SemanticKernelHeadersPolicy : HttpPipelineSynchronousPolicy
    {
        public override void OnSendingRequest(HttpMessage message)
        {
            message.Request.Headers.Add(
                HttpHeaderConstant.Names.UserAgent,
                $"{HttpHeaderConstant.Values.UserAgent} {nameof(AzureAIAgent)}");

            message.Request.Headers.Add(
                HttpHeaderConstant.Names.SemanticKernelVersion,
                HttpHeaderConstant.Values.GetAssemblyVersion(typeof(AzureAIAgent)));
        }
    }
}
