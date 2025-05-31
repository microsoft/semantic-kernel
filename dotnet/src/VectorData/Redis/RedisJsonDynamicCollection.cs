// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Represents a collection of vector store records in a Redis JSON database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class RedisJsonDynamicCollection : RedisJsonCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="RedisJsonDynamicCollection"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The Redis provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Redis provider is currently incompatible with NativeAOT.")]
    public RedisJsonDynamicCollection(IDatabase database, string name, RedisJsonCollectionOptions options)
        : base(
            database,
            name,
            static options => new RedisJsonDynamicModelBuilder(ModelBuildingOptions)
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("Definition is required for dynamic collections"),
                    options.EmbeddingGenerator),
            options)
    {
    }
}
