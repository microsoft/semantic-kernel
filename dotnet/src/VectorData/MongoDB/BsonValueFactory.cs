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
    {
        if (value is null)
        {
            return BsonNull.Value;
        }

        if (value.GetType().IsArray)
        {
            if (value is Guid[] guids)
            {
                return new BsonArray(Array.ConvertAll(guids, x => new BsonBinaryData(x, GuidRepresentation.Standard)));
            }

            return new BsonArray(value as Array);
        }

        if (value is Guid guid)
        {
            return new BsonBinaryData(guid, GuidRepresentation.Standard);
        }

        return BsonValue.Create(value);
    }
}
