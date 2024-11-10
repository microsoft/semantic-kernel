﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Constants for MongoDB vector store implementation.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class MongoDBConstants
{
    /// <summary>Default ratio of number of nearest neighbors to number of documents to return.</summary>
    internal const int DefaultNumCandidatesRatio = 10;

    /// <summary>Default vector index name.</summary>
    internal const string DefaultVectorIndexName = "vector_index";

    /// <summary>Default index kind for vector search.</summary>
    internal const string DefaultIndexKind = IndexKind.IvfFlat;

    /// <summary>Default distance function for vector search.</summary>
    internal const string DefaultDistanceFunction = DistanceFunction.CosineDistance;

    /// <summary>Reserved key property name in MongoDB.</summary>
    internal const string MongoReservedKeyPropertyName = "_id";

    /// <summary>Reserved key property name in data model.</summary>
    internal const string DataModelReservedKeyPropertyName = "Id";

    /// <summary>A <see cref="HashSet{Type}"/> containing the supported key types.</summary>
    internal static readonly HashSet<Type> SupportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A <see cref="HashSet{Type}"/> containing the supported data property types.</summary>
    internal static readonly HashSet<Type> SupportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(string),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(DateTime),
        typeof(DateTime?),
    ];

    /// <summary>A <see cref="HashSet{Type}"/> containing the supported vector types.</summary>
    internal static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];
}
