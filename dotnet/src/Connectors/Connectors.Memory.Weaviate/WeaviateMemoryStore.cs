<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> origin/main
using Microsoft.SemanticKernel.Memory;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
>>>>>>> main
=======
>>>>>>> head

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// An implementation of <see cref="IMemoryStore" /> for Weaviate.
/// </summary>
/// <remarks>The Embedding data is saved to Weaviate instance specified in the constructor.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
// ReSharper disable once ClassWithVirtualMembersNeverInherited.Global
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public partial class WeaviateMemoryStore : IMemoryStore
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    /// <summary>
    /// The authorization header name
    /// </summary>
    private const string AuthorizationHeaderName = nameof(HttpRequestHeader.Authorization);

    // Regex to ensure Weaviate class names confirm to the naming convention
    // https://weaviate.io/developers/weaviate/configuration/schema-configuration#class
#if NET
    [GeneratedRegex("[^0-9a-zA-Z]+")]
    private static partial Regex ClassNameRegex();
#else
    private static Regex ClassNameRegex() => s_classNameRegex;
    private static readonly Regex s_classNameRegex = new("[^0-9a-zA-Z]+", RegexOptions.Compiled);
#endif

    private const string DefaultApiVersion = "v1";

    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Converters = { JsonOptionsCache.ReadOnlyMemoryConverter }
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
    };

    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly Uri? _endpoint = null;
    private readonly string? _apiVersion;
    private readonly string? _apiKey;
    private static readonly string[] s_stringArray = ["vector"];

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryStore"/> class.
    /// </summary>
    /// <param name="endpoint">The Weaviate server endpoint URL.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WeaviateMemoryStore(
        string endpoint,
        string? apiKey = null,
        string? apiVersion = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(endpoint);

        this._endpoint = new Uri(endpoint);
        this._apiKey = apiKey;
        this._apiVersion = apiVersion;
        this._logger = loggerFactory?.CreateLogger(typeof(WeaviateMemoryStore)) ?? NullLogger.Instance;
        this._httpClient = HttpClientProvider.GetHttpClient();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateMemoryStore"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="endpoint">The optional Weaviate server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public WeaviateMemoryStore(
        HttpClient httpClient,
        string? apiKey = null,
        string? endpoint = null,
        string? apiVersion = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(httpClient);

        if (string.IsNullOrEmpty(httpClient.BaseAddress?.AbsoluteUri) && string.IsNullOrEmpty(endpoint))
        {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
            throw new ArgumentException($"The {nameof(httpClient)}.{nameof(HttpClient.BaseAddress)} and {nameof(endpoint)} are both null or empty. Please ensure at least one is provided.");
=======
            throw new ArgumentException("The HttpClient BaseAddress and endpoint are both null or empty. Please ensure at least one is provided.");
>>>>>>> ms/feature-error-handling
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
        }

        this._apiKey = apiKey;
        this._apiVersion = apiVersion;
        this._endpoint = string.IsNullOrEmpty(endpoint) ? null : new Uri(endpoint);
        this._logger = loggerFactory?.CreateLogger(typeof(WeaviateMemoryStore)) ?? NullLogger.Instance;
        this._httpClient = httpClient;
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");

        string className = ToWeaviateFriendlyClassName(collectionName);
        string description = ToWeaviateFriendlyClassDescription(collectionName);

        this._logger.LogDebug("Creating collection: {0}, with class name: {1}", collectionName, className);

        using HttpRequestMessage request = CreateClassSchemaRequest.Create(className, description).Build();

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        try
        {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            CreateClassSchemaResponse? result = JsonSerializer.Deserialize<CreateClassSchemaResponse>(responseContent, s_jsonOptionsCache);

            if (result is null || result.Description != description)
            {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                throw new KernelException($"Name conflict for collection: {collectionName} with class name: {className}");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
                throw new KernelException($"Name conflict for collection: {collectionName} with class name: {className}");
=======
                throw new SKException($"Name conflict for collection: {collectionName} with class name: {className}");
>>>>>>> ms/feature-error-handling-part3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
            }

            this._logger.LogDebug("Created collection: {0}, with class name: {1}", collectionName, className);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to create collection: {CollectionName}, with class name: {ClassName}", collectionName, className);
            throw;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to create collection: {0}, with class name: {1}", collectionName, className);
            throw;
        }

        CreateClassSchemaResponse? result = JsonSerializer.Deserialize<CreateClassSchemaResponse>(responseContent, s_jsonSerializerOptions);

        if (result == null || result.Description != description)
        {
<<<<<<< main
            throw new SKException($"Name conflict for collection: {collectionName} with class name: {className}");
>>>>>>> ms/feature-error-handling
=======
            throw new SKException($"Unable to create collection: {collectionName}, with class name: {className}", e);
>>>>>>> ms/feature-error-handling-part3
        }

        this._logger.LogDebug("Created collection: {0}, with class name: {1}", collectionName, className);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to create collection: {0}, with class name: {1}", collectionName, className);
            throw;
        }

        CreateClassSchemaResponse? result = JsonSerializer.Deserialize<CreateClassSchemaResponse>(responseContent, s_jsonSerializerOptions);

        if (result == null || result.Description != description)
        {
<<<<<<< main
            throw new SKException($"Name conflict for collection: {collectionName} with class name: {className}");
>>>>>>> ms/feature-error-handling
=======
            throw new SKException($"Unable to create collection: {collectionName}, with class name: {className}", e);
>>>>>>> ms/feature-error-handling-part3
        }

        this._logger.LogDebug("Created collection: {0}, with class name: {1}", collectionName, className);
<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");

        string className = ToWeaviateFriendlyClassName(collectionName);

        this._logger.LogDebug("Does collection exist: {CollectionName}, with class name: {ClassName}:", collectionName, className);

        using HttpRequestMessage request = GetClassRequest.Create(className).Build();

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        try
        {
            (_, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            GetClassResponse? existing = JsonSerializer.Deserialize<GetClassResponse>(responseContent, s_jsonOptionsCache);

            if (existing is not null && existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
            {
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
                // ReSharper disable once CommentTypo
                // Check that we don't have an accidental conflict.
                // For example a collectionName of '__this_collection' and 'this_collection' are
                // both transformed to the class name of <classNamePrefix>thiscollection - even though the external
                // system could consider them as unique collection names.
                throw new KernelException($"Unable to verify existing collection: {collectionName} with class name: {className}");
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
                GetClassResponse? existing = JsonSerializer.Deserialize<GetClassResponse>(responseContent, s_jsonSerializerOptions);
                if (existing != null && existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
                {
                    // ReSharper disable once CommentTypo
                    // Check that we don't have an accidental conflict.
                    // For example a collectionName of '__this_collection' and 'this_collection' are
                    // both transformed to the class name of <classNamePrefix>thiscollection - even though the external
                    // system could consider them as unique collection names.
                    throw new SKException($"Unable to verify existing collection: {collectionName} with class name: {className}");
                }
>>>>>>> ms/feature-error-handling-part3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
            }

            return true;
        }
        catch (HttpOperationException e) when (e.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogDebug(e, "Collection: {CollectionName}, with class name: {ClassName}, does not exist.", collectionName, className);
            return false;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Request to check collection: {CollectionName}, with class name: {ClassName} existence failed.", collectionName, className);
            throw;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogTrace("Collection: {0}, with class name: {1}, does not exist.", collectionName, className);
            return false;
        }

        try
        {
<<<<<<< main
            response.EnsureSuccess(responseContent, this._logger);
=======
            throw new SKException("Unable to get class from Weaviate", e);
>>>>>>> ms/feature-error-handling-part3
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to verify existing collection: {0}, with class name: {1}", collectionName, className);
            throw;
        }

        GetClassResponse? existing = JsonSerializer.Deserialize<GetClassResponse>(responseContent, s_jsonSerializerOptions);
        if (existing != null && existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
        {
            throw new SKException($"Unable to verify existing collection: {collectionName} with class name: {className}");
>>>>>>> ms/feature-error-handling
        }

        return true;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogTrace("Collection: {0}, with class name: {1}, does not exist.", collectionName, className);
            return false;
        }

        try
        {
<<<<<<< main
            response.EnsureSuccess(responseContent, this._logger);
=======
            throw new SKException("Unable to get class from Weaviate", e);
>>>>>>> ms/feature-error-handling-part3
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to verify existing collection: {0}, with class name: {1}", collectionName, className);
            throw;
        }

        GetClassResponse? existing = JsonSerializer.Deserialize<GetClassResponse>(responseContent, s_jsonSerializerOptions);
        if (existing != null && existing.Description != ToWeaviateFriendlyClassDescription(collectionName))
        {
            throw new SKException($"Unable to verify existing collection: {collectionName} with class name: {className}");
>>>>>>> ms/feature-error-handling
        }

        return true;
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Listing collections");

        using HttpRequestMessage request = GetSchemaRequest.Create().Build();

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        string responseContent;

        try
        {
            (HttpResponseMessage response, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
            this._logger.LogError(e, "Request to list collections failed.");
            throw;
        }

        GetSchemaResponse getSchemaResponse = JsonSerializer.Deserialize<GetSchemaResponse>(responseContent, s_jsonOptionsCache) ??
            throw new KernelException("Unable to deserialize list collections response");
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Unable to list collections");
            throw;
=======
            throw new SKException("Unable to list collections", e);
>>>>>>> ms/feature-error-handling-part3
        }

        GetSchemaResponse? getSchemaResponse = JsonSerializer.Deserialize<GetSchemaResponse>(responseContent, s_jsonSerializerOptions);
        if (getSchemaResponse == null)
        {
<<<<<<< Updated upstream
            throw new SKException("Unable to deserialize list collections response");
        }
>>>>>>> ms/feature-error-handling
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
            throw new SKException("Unable to deserialize list collections response");
        }
>>>>>>> ms/feature-error-handling
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        foreach (GetClassResponse? @class in getSchemaResponse.Classes!)
        {
            yield return @class.Class!;
        }
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");

        string className = ToWeaviateFriendlyClassName(collectionName);

        this._logger.LogDebug("Deleting collection: {0}, with class name: {1}", collectionName, className);

        if (await this.DoesCollectionExistAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            using HttpRequestMessage request = DeleteSchemaRequest.Create(className).Build();

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
            try
            {
                await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
            }
            catch (HttpOperationException e)
            {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
                this._logger.LogError(e, "Request to delete collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
=======
            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            try
            {
                response.EnsureSuccess(responseContent, this._logger);
            }
            catch (HttpOperationException e)
            {
                this._logger.LogError(e, "Collection deletion failed");
>>>>>>> ms/feature-error-handling
                throw;
=======
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
                this._logger.LogError(e, "Request to delete collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
=======
            (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            try
            {
                response.EnsureSuccess(responseContent, this._logger);
            }
            catch (HttpOperationException e)
            {
                this._logger.LogError(e, "Collection deletion failed");
>>>>>>> ms/feature-error-handling
                throw;
=======
                throw new SKException("Collection deletion failed", e);
>>>>>>> ms/feature-error-handling-part3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                throw new SKException("Collection deletion failed", e);
>>>>>>> ms/feature-error-handling-part3
>>>>>>> origin/main
=======
                throw new SKException("Collection deletion failed", e);
>>>>>>> ms/feature-error-handling-part3
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
                throw new SKException("Collection deletion failed", e);
>>>>>>> ms/feature-error-handling-part3
>>>>>>> main
=======
>>>>>>> head
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");

        return await this.UpsertBatchAsync(collectionName, [record], cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");

        this._logger.LogDebug("Upsert vectors");

        string className = ToWeaviateFriendlyClassName(collectionName);
        BatchRequest requestBuilder = BatchRequest.Create(className);
        foreach (MemoryRecord? record in records)
        {
            requestBuilder.Add(record);
        }

        using HttpRequestMessage request = requestBuilder.Build();

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> head
        string responseContent;

        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
            this._logger.LogError(e, "Request to upsert vectors to collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
            throw;
        }

        BatchResponse[] result = JsonSerializer.Deserialize<BatchResponse[]>(responseContent, s_jsonOptionsCache) ??
            throw new KernelException("Unable to deserialize batch response");
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Failed to upsert vectors");
            throw;
=======
            throw new SKException("Failed to upsert vectors", e);
>>>>>>> ms/feature-error-handling-part3
        }

        BatchResponse[]? result = JsonSerializer.Deserialize<BatchResponse[]>(responseContent, s_jsonSerializerOptions);

        if (result == null)
        {
            throw new SKException("Unable to deserialize batch response");
        }
>>>>>>> ms/feature-error-handling
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        foreach (BatchResponse batchResponse in result)
        {
            yield return batchResponse.Id!;
        }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");
        Verify.NotNullOrWhiteSpace(key, "Key is empty");

        using HttpRequestMessage request = new GetObjectRequest
        {
            Id = key,
            Additional = withEmbedding ? s_stringArray : null
        }.Build();

        string responseContent;

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> head
        try
        {
            (_, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Request to get vector from collection: {CollectionName} failed.", collectionName);
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            return null;
        }
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        (HttpResponseMessage response, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException) when (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogDebug("No vector with key: {0} is found", key);
>>>>>>> ms/feature-error-handling
            return null;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError("Request for vector failed {0}", e.Message);
            throw;
        }
<<<<<<< div
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> head
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

=======
=======
        (HttpResponseMessage response, responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException) when (response.StatusCode == HttpStatusCode.NotFound)
        {
            this._logger.LogDebug("No vector with key: {0} is found", key);
>>>>>>> ms/feature-error-handling
            return null;
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError("Request for vector failed {0}", e.Message);
            throw;
        }

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        WeaviateObject? weaviateObject = JsonSerializer.Deserialize<WeaviateObject>(responseContent, s_jsonOptionsCache);
        if (weaviateObject is null)
        {
            this._logger.LogError("Unable to deserialize response to WeaviateObject");
            return null;
        }

        DateTimeOffset? timestamp = weaviateObject.Properties is null
            ? null
            : weaviateObject.Properties.TryGetValue("sk_timestamp", out object? value)
                ? Convert.ToDateTime(value.ToString(), CultureInfo.InvariantCulture)
                : null;

        MemoryRecord record = new(
            key: weaviateObject.Id,
            timestamp: timestamp,
            embedding: weaviateObject.Vector,
            metadata: ToMetadata(weaviateObject));

        this._logger.LogDebug("Vector found with key: {0}", key);

        return record;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (string? key in keys)
        {
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
            if (record is not null)
            {
                yield return record;
            }
            else
            {
                this._logger.LogWarning("Unable to locate object with id: {0}", key);
            }
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName, "Collection name is empty");
        Verify.NotNull(key, "Key is NULL");

        string className = ToWeaviateFriendlyClassName(collectionName);

        this._logger.LogDebug("Deleting vector with key: {0}, from collection {1}, with class name: {2}:", key, collectionName, className);

        DeleteObjectRequest requestBuilder = new()
        {
            Class = className,
            Id = key
        };

        using HttpRequestMessage request = requestBuilder.Build();

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        try
        {
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
<<<<<<< main
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

            this._logger.LogDebug("Vector deleted");
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Request to delete collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
<<<<<<< main
            this._logger.LogError(e, "Vector delete request failed");
>>>>>>> ms/feature-error-handling
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
            throw;
=======
            throw new SKException("Vector delete request failed", e);
>>>>>>> ms/feature-error-handling-part3
        }
<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
>>>>>>> head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
<<<<<<< main
            this._logger.LogError(e, "Vector delete request failed");
>>>>>>> ms/feature-error-handling
            throw;
=======
            throw new SKException("Vector delete request failed", e);
>>>>>>> ms/feature-error-handling-part3
        }

        this._logger.LogDebug("Vector deleted");
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

        this._logger.LogDebug("Vector deleted");
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======

        this._logger.LogDebug("Vector deleted");
>>>>>>> main
=======
>>>>>>> head
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancellationToken).ConfigureAwait(false))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(embedding, "The given vector is NULL");

        this._logger.LogDebug("Searching top {Limit} nearest vectors", limit);

        string className = ToWeaviateFriendlyClassName(collectionName);

        using HttpRequestMessage request = new CreateGraphRequest
        {
            Class = className,
            Vector = embedding,
            Distance = minRelevanceScore,
            Limit = limit,
            WithVector = withEmbeddings
        }.Build();

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        List<(MemoryRecord, double)> result = [];
        try
        {
            (_, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
        List<(MemoryRecord, double)> result = new();

<<<<<<< main
=======
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
=======
=======
        List<(MemoryRecord, double)> result = new();

<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        (HttpResponseMessage response, string responseContent) = await this.ExecuteHttpRequestAsync(request, cancellationToken).ConfigureAwait(false);

        try
        {
            response.EnsureSuccess(responseContent, this._logger);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Nearest vectors search failed: {0}", e.Message);
            throw;
        }
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head

        try
        {
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonSerializerOptions);
>>>>>>> ms/feature-error-handling

>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonOptionsCache);

=======
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

        try
        {
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonSerializerOptions);
>>>>>>> ms/feature-error-handling

<<<<<<< div
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonOptionsCache);

>>>>>>> main
=======
<<<<<<< Updated upstream
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonOptionsCache);

>>>>>>> origin/main
=======
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonOptionsCache);

>>>>>>> Stashed changes
=======
>>>>>>> origin/main
            GraphResponse? data = JsonSerializer.Deserialize<GraphResponse>(responseContent, s_jsonOptionsCache);

>>>>>>> Stashed changes
>>>>>>> head
            if (data is null)
            {
                this._logger.LogWarning("Unable to deserialize Search response");
                yield break;
            }

            JsonArray jsonArray = data.Data["Get"]![className]!.AsArray();

            // ReSharper disable once LoopCanBeConvertedToQuery
            foreach (JsonNode? json in jsonArray)
            {
                MemoryRecord memoryRecord = DeserializeToMemoryRecord(json);
                double distance = json!["_additional"]!["distance"]!.GetValue<double>();
                result.Add((memoryRecord, distance));
            }
        }
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Request to find nearest vector in collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
            throw;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
        catch (HttpOperationException e)
        {
<<<<<<< main
            this._logger.LogError(e, "Request to find nearest vector in collection: {CollectionName}, with class name: {ClassName} failed.", collectionName, className);
            throw;
=======
            throw new SKException("Unable to deserialize Weaviate object", e);
>>>>>>> ms/feature-error-handling
=======
        catch (Exception e)
        {
            throw new SKException("Unable to deserialize Weaviate object", e);
>>>>>>> ms/feature-error-handling-part3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
        }

        foreach ((MemoryRecord, double) kv in result)
        {
            yield return kv;
        }
    }

    private static MemoryRecord DeserializeToMemoryRecord(JsonNode? json)
    {
        string id = json!["_additional"]!["id"]!.GetValue<string>();
        ReadOnlyMemory<float> vector = ReadOnlyMemory<float>.Empty;
        if (json["_additional"]!["vector"] is JsonArray jsonArray)
        {
            vector = jsonArray.Select(a => a!.GetValue<float>()).ToArray();
        }

        string text = json["sk_text"]!.GetValue<string>();
        string description = json["sk_description"]!.GetValue<string>();
        string additionalMetadata = json["sk_additional_metadata"]!.GetValue<string>();
        string key = json["sk_id"]!.GetValue<string>();
        DateTime? timestamp = json["sk_timestamp"] is not null
            ? Convert.ToDateTime(json["sk_timestamp"]!.GetValue<string>(), CultureInfo.InvariantCulture)
            : null;

        MemoryRecord memoryRecord = MemoryRecord.LocalRecord(
            id,
            text,
            description,
            vector,
            additionalMetadata,
            key,
            timestamp);
        return memoryRecord;
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        IAsyncEnumerable<(MemoryRecord, double)> results = this.GetNearestMatchesAsync(
            collectionName,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken);

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

        return (record.Item1, record.Item2);
    }

    // Get a class description, useful for checking name collisions
    private static string ToWeaviateFriendlyClassDescription(string collectionName)
    {
        return $"Semantic Kernel memory store for collection: {collectionName}";
    }

    // Convert a collectionName to a valid Weaviate class name
    private static string ToWeaviateFriendlyClassName(string collectionName)
    {
        // Prefix class names with to ensure proper case for Weaviate Classes
        var sanitised = ClassNameRegex().Replace(collectionName, string.Empty);
        if (!char.IsLetter(sanitised[0]))
        {
            throw new ArgumentException("collectionName must start with a letter.", nameof(collectionName));
        }

        return !char.IsUpper(sanitised[0])
            ? string.Concat(sanitised[0].ToString().ToUpper(CultureInfo.InvariantCulture), sanitised.Substring(1))
            : sanitised;
    }

    // Execute the HTTP request
    private async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(
        HttpRequestMessage request,
        CancellationToken cancel = default)
    {
        var apiVersion = !string.IsNullOrWhiteSpace(this._apiVersion) ? this._apiVersion : DefaultApiVersion;
        var baseAddress = this._endpoint ?? this._httpClient.BaseAddress;

        request.RequestUri = new Uri(baseAddress!, $"{apiVersion}/{request.RequestUri}");

        if (!string.IsNullOrEmpty(this._apiKey))
        {
            request.Headers.Add(AuthorizationHeaderName, this._apiKey);
        }

        try
        {
            HttpResponseMessage response = await this._httpClient.SendWithSuccessCheckAsync(request, cancel).ConfigureAwait(false);

            string? responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

            this._logger.LogDebug("Weaviate responded with {StatusCode}", response.StatusCode);

            return (response, responseContent);
        }
        catch (HttpOperationException e)
        {
            this._logger.LogError(e, "Weaviate responded with {StatusCode}", e.StatusCode);
            throw;
        }
    }

    private static MemoryRecordMetadata ToMetadata(WeaviateObject weaviateObject)
    {
        Verify.NotNull(weaviateObject.Properties, "weaviateObject.Properties");

        return new(
            false,
            string.Empty,
            weaviateObject.Properties["sk_id"].ToString() ?? string.Empty,
            weaviateObject.Properties["sk_description"].ToString() ?? string.Empty,
            weaviateObject.Properties["sk_text"].ToString() ?? string.Empty,
            weaviateObject.Properties["sk_additional_metadata"].ToString() ?? string.Empty
        );
    }
}
