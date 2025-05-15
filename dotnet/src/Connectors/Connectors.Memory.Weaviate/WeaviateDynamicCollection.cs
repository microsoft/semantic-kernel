// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Represents a collection of vector store records in a Weaviate database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class WeaviateDynamicCollection : WeaviateCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateDynamicCollection"/> class.
    /// </summary>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateCollectionOptions"/>.
    /// </param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The Weaviate provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Weaviate provider is currently incompatible with NativeAOT.")]
    public WeaviateDynamicCollection(HttpClient httpClient, string name, WeaviateCollectionOptions options)
        : base(
            httpClient,
            name,
            static options => new WeaviateModelBuilder(options.HasNamedVectors)
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                    options.EmbeddingGenerator,
                    WeaviateConstants.s_jsonSerializerOptions),
            options)
    {
    }
}
