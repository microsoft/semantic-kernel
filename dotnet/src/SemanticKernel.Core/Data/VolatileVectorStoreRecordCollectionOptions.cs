// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options when creating a <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/>.
/// </summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
[Experimental("SKEXP0001")]
public sealed class VolatileVectorStoreRecordCollectionOptions
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
[Experimental("SKEXP0001")]
public sealed class VolatileVectorStoreRecordCollectionOptions
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
[Experimental("SKEXP0001")]
public sealed class VolatileVectorStoreRecordCollectionOptions
=======
>>>>>>> Stashed changes
/// <typeparam name="TKey">The data type of the record key of the collection that this options will be used with.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data on the collection that this options will be used with.</typeparam>
[Experimental("SKEXP0001")]
public sealed class VolatileVectorStoreRecordCollectionOptions<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
{
    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;
<<<<<<< HEAD
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
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

    /// <summary>
    /// An optional function that can be used to look up vectors from a record.
    /// </summary>
    /// <remarks>
    /// If not provided, the default behavior is to look for direct properties of the record
    /// using reflection. This delegate can be used to provide a custom implementation if
    /// the vector properties are located somewhere else on the record.
    /// </remarks>
    public VolatileVectorStoreVectorResolver<TRecord>? VectorResolver { get; init; } = null;

    /// <summary>
    /// An optional function that can be used to look up record keys.
    /// </summary>
    /// <remarks>
    /// If not provided, the default behavior is to look for a direct property of the record
    /// using reflection. This delegate can be used to provide a custom implementation if
    /// the key property is located somewhere else on the record.
    /// </remarks>
    public VolatileVectorStoreKeyResolver<TKey, TRecord>? KeyResolver { get; init; } = null;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
