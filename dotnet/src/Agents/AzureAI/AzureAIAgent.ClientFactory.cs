// Copyright (c) Microsoft. All rights reserved.
using System.Net.Http;
using Azure.AI.Projects;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides an <see cref="AIProjectClient"/> for use by <see cref="AzureAIAgent"/>.
/// </summary>
public sealed partial class AzureAIAgent : Agent
{
    /// <summary>
    /// Produces a <see cref="AIProjectClient"/>.
    /// </summary>
    /// <param name="connectionString">The Azure AI Foundry project connection string, in the form `endpoint;subscription_id;resource_group_name;project_name`.</param>
    /// <param name="credential"> A credential used to authenticate to an Azure Service.</param>
    /// <param name="httpClient">A custom <see cref="HttpClient"/> for HTTP requests.</param>
    public static AIProjectClient CreateAzureAIClient(
        string connectionString,
        TokenCredential credential,
        HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString, nameof(connectionString));
        Verify.NotNull(credential, nameof(credential));

        AIProjectClientOptions clientOptions = CreateAzureClientOptions(httpClient);

        return new AIProjectClient(connectionString, credential, clientOptions);
    }

    private static AIProjectClientOptions CreateAzureClientOptions(HttpClient? httpClient)
    {
        AIProjectClientOptions options = new();

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
