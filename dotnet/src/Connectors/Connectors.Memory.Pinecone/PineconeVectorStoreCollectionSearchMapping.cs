// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Contains mapping helpers to use when searching a Pinecone vector collection.
/// </summary>
internal static class PineconeVectorStoreCollectionSearchMapping
{
#pragma warning disable CS0618 // FilterClause is obsolete
    /// <summary>
    /// Build a Pinecone <see cref="Metadata"/> from a set of filter clauses.
    /// </summary>
    /// <param name="filterClauses">The filter clauses to build the Pinecone <see cref="Metadata"/> from.</param>
    /// <param name="model">The model.</param>
    /// <returns>The Pinecone <see cref="Metadata"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown for invalid property names, value types or filter clause types.</exception>
    public static Metadata BuildSearchFilter(IEnumerable<FilterClause>? filterClauses, VectorStoreRecordModel model)
    {
        var metadataMap = new Metadata();

        if (filterClauses is null)
        {
            return metadataMap;
        }

        foreach (var filterClause in filterClauses)
        {
            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                if (!model.PropertyMap.TryGetValue(equalToFilterClause.FieldName, out var property))
                {
                    throw new InvalidOperationException($"Property '{equalToFilterClause.FieldName}' is not a valid property name.");
                }

                var metadataValue = equalToFilterClause.Value switch
                {
                    string stringValue => (MetadataValue)stringValue,
                    int intValue => (MetadataValue)intValue,
                    long longValue => (MetadataValue)longValue,
                    bool boolValue => (MetadataValue)boolValue,
                    float floatValue => (MetadataValue)floatValue,
                    double doubleValue => (MetadataValue)doubleValue,
                    _ => throw new NotSupportedException($"Unsupported filter value type '{equalToFilterClause.Value.GetType().Name}'.")
                };

                metadataMap.Add(property.StorageName, metadataValue);
            }
            else
            {
                throw new NotSupportedException($"Unsupported filter clause type '{filterClause.GetType().Name}'.");
            }
        }

        return metadataMap;
    }
#pragma warning restore CS0618 // FilterClause is obsolete
}
