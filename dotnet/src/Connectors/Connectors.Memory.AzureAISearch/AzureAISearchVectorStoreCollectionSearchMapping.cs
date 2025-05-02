// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Azure AI Search.
/// </summary>
internal static class AzureAISearchVectorStoreCollectionSearchMapping
{
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <summary>
    /// Build an OData filter string from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="basicVectorSearchFilter">The <see cref="VectorSearchFilter"/> to build an OData filter string from.</param>
    /// <param name="model">The model.</param>
    /// <returns>The OData filter string.</returns>
    /// <exception cref="InvalidOperationException">Thrown when a provided filter value is not supported.</exception>
    public static string BuildLegacyFilterString(VectorSearchFilter basicVectorSearchFilter, VectorStoreRecordModel model)
    {
        var filterString = string.Empty;
        if (basicVectorSearchFilter.FilterClauses is not null)
        {
            // Map Equality clauses.
            var filterStrings = basicVectorSearchFilter?.FilterClauses.OfType<EqualToFilterClause>().Select(x =>
            {
                string storageFieldName = GetStoragePropertyName(model, x.FieldName);

                return x.Value switch
                {
                    string stringValue => $"{storageFieldName} eq '{stringValue}'",
#pragma warning disable CA1308 // Normalize strings to uppercase - OData filter strings use lowercase boolean literals. See https://docs.oasis-open.org/odata/odata/v4.01/cs01/part2-url-conventions/odata-v4.01-cs01-part2-url-conventions.html#sec_PrimitiveLiterals
                    bool boolValue => $"{storageFieldName} eq {boolValue.ToString().ToLowerInvariant()}",
#pragma warning restore CA1308 // Normalize strings to uppercase
                    int intValue => $"{storageFieldName} eq {intValue}",
                    long longValue => $"{storageFieldName} eq {longValue}",
                    float floatValue => $"{storageFieldName} eq {floatValue}",
                    double doubleValue => $"{storageFieldName} eq {doubleValue}",
                    DateTimeOffset dateTimeOffsetValue => $"{storageFieldName} eq {dateTimeOffsetValue.UtcDateTime:O}",
                    null => $"{storageFieldName} eq null",
                    _ => throw new InvalidOperationException($"Unsupported filter value type '{x.Value.GetType().Name}'.")
                };
            });

            // Map tag contains clauses.
            var tagListContainsStrings = basicVectorSearchFilter?.FilterClauses
                .OfType<AnyTagEqualToFilterClause>()
                .Select(x => $"{GetStoragePropertyName(model, x.FieldName)}/any(t: t eq '{x.Value}')");

            // Combine clauses.
            filterString = string.Join(" and ", filterStrings!.Concat(tagListContainsStrings!));
        }

        return filterString;
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    /// <summary>
    /// Gets the name of the name under which the property with the given name is stored.
    /// </summary>
    /// <param name="model">The model.</param>
    /// <param name="fieldName">The name of the property in the data model.</param>
    /// <returns>The name that the property os stored under.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the property name is not found.</exception>
    private static string GetStoragePropertyName(VectorStoreRecordModel model, string fieldName)
    {
        if (!model.PropertyMap.TryGetValue(fieldName, out var property))
        {
            throw new InvalidOperationException($"Property name '{fieldName}' provided as part of the filter clause is not a valid property name.");
        }

        return property.StorageName;
    }
}
