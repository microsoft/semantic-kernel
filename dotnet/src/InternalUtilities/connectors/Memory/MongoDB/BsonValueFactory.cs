// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
            object[] array => new BsonArray(Array.ConvertAll(array, Create)),
            Array array => new BsonArray(array),
            IEnumerable<object> enumerable => new BsonArray(enumerable.Select(Create)),
            _ => BsonValue.Create(value)
        };
}
