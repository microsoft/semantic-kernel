// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class ListCollectionsResponse : QdrantResponse
{
    internal sealed class CollectionResult
    {
        internal sealed class CollectionDescription
        {
            /// <summary>
            /// The name of a collection
            /// </summary>
            [JsonPropertyName("name")]
            public string Name { get; set; } = string.Empty;
        }

        /// <summary>
        /// List of the collection names that the qdrant database contains.
        /// </summary>
        [JsonPropertyName("collections")]
        public IList<CollectionDescription> Collections { get; set; } = [];
    }

    /// <summary>
    /// Result containing a list of collection names
    /// </summary>
    [JsonPropertyName("result")]
    public CollectionResult? Result { get; set; }
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
