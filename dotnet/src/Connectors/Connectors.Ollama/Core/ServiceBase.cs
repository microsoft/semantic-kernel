// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using OllamaSharp;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Represents the core of a service.
/// </summary>
public abstract class ServiceBase
{
    /// <summary>
    /// Attributes of the service.
    /// </summary>
    internal Dictionary<string, object?> AttributesInternal { get; } = new();
    internal readonly OllamaApiClient _client;

    internal ServiceBase(string model,
        Uri endpoint,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);

        if (httpClient is not null)
        {
            httpClient.BaseAddress ??= endpoint;

            // Try to add User-Agent header.
            if (!httpClient.DefaultRequestHeaders.TryGetValues("User-Agent", out _))
            {
                httpClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
            }

            // Try to add Semantic Kernel Version header 
            if (!httpClient.DefaultRequestHeaders.TryGetValues(HttpHeaderConstant.Names.SemanticKernelVersion, out _))
            {
                httpClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(Kernel)));
            }

            this._client = new(httpClient, model);
        }
        else
        {
#pragma warning disable CA2000 // Dispose objects before losing scope
            // Client needs to be created to be able to inject Semantic Kernel headers
            var internalClient = HttpClientProvider.GetHttpClient();
            internalClient.BaseAddress = endpoint;
            internalClient.DefaultRequestHeaders.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
            internalClient.DefaultRequestHeaders.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(Kernel)));

            this._client = new(internalClient, model);
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
    }

    internal ServiceBase(string model,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        this._client = ollamaClient;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }
}
