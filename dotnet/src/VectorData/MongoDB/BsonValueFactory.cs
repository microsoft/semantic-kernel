// Copyright (c) Microsoft. All rights reserved.

using System;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// A class that constructs the correct BsonValue for a given CLR type.
/// </summary>
internal static class BsonValueFactory
{
    /// <summary>
    /// Create a BsonValue for the given CLR type.
    /// </summary>
    /// <param name="value">The CLR object to create a BSON value for.</param>
    /// <returns>The appropriate <see cref="BsonValue"/> for that CLR type.</returns>
    public static BsonValue Create(object? value)
        => value switch
        {
            null => BsonNull.Value,
            Guid guid => new BsonBinaryData(guid, GuidRepresentation.Standard),
            Guid[] guids => new BsonArray(Array.ConvertAll(guids, x => new BsonBinaryData(x, GuidRepresentation.Standard))),
            Array array => new BsonArray(array),
            _ => BsonValue.Create(value)
        };
}
