// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Numerics.Tensors;
using System.Reflection;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Contains mapping helpers to use when searching for documents using the InMemory store.
/// </summary>
internal static class InMemoryVectorStoreCollectionSearchMapping
{
    /// <summary>
    /// Compare the two vectors using the specified distance function.
    /// </summary>
    /// <param name="x">The first vector to compare.</param>
    /// <param name="y">The second vector to compare.</param>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>The score of the comparison.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static float CompareVectors(ReadOnlySpan<float> x, ReadOnlySpan<float> y, string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.CosineDistance:
                return TensorPrimitives.CosineSimilarity(x, y);
            case DistanceFunction.DotProductSimilarity:
                return TensorPrimitives.Dot(x, y);
            case DistanceFunction.EuclideanDistance:
                return TensorPrimitives.Distance(x, y);
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }

    /// <summary>
    /// Indicates whether result ordering should be descending or ascending, to get most similar results at the top, based on the distance function.
    /// </summary>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>Whether to order descending or ascending.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static bool ShouldSortDescending(string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.DotProductSimilarity:
                return true;
            case DistanceFunction.CosineDistance:
            case DistanceFunction.EuclideanDistance:
                return false;
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }

    /// <summary>
    /// Converts the provided score into the correct result depending on the distance function.
    /// The main purpose here is to convert from cosine similarity to cosine distance if cosine distance is requested,
    /// since the two are inversely related and the <see cref="TensorPrimitives"/> only supports cosine similarity so
    /// we are using cosine similarity for both similarity and distance.
    /// </summary>
    /// <param name="score">The score to convert.</param>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>Whether to order descending or ascending.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static float ConvertScore(float score, string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case DistanceFunction.CosineDistance:
                return 1 - score;
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.DotProductSimilarity:
            case DistanceFunction.EuclideanDistance:
                return score;
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <summary>
    /// Filter the provided records using the provided filter definition.
    /// </summary>
    /// <param name="filter">The filter definition to filter the <paramref name="recordWrappers"/> with.</param>
    /// <param name="recordWrappers">The records to filter.</param>
    /// <returns>The filtered records.</returns>
    /// <exception cref="InvalidOperationException">Thrown when an unsupported filter clause is encountered.</exception>
    public static IEnumerable<InMemoryVectorRecordWrapper<TRecord>> FilterRecords<TRecord>(VectorSearchFilter filter, IEnumerable<InMemoryVectorRecordWrapper<TRecord>> recordWrappers)
    {
        return recordWrappers.Where(wrapper =>
        {
            if (wrapper.Record is null)
            {
                return false;
            }

            var result = true;

            // Run each filter clause against the record, and AND the results together.
            // Break if any clause returns false, since we are doing an AND and no need
            // to check any further clauses.
            foreach (var clause in filter.FilterClauses)
            {
                if (clause is EqualToFilterClause equalToFilter)
                {
                    result = result && CheckEqualTo(wrapper.Record, equalToFilter);

                    if (result == false)
                    {
                        break;
                    }
                }
                else if (clause is AnyTagEqualToFilterClause anyTagEqualToFilter)
                {
                    result = result && CheckAnyTagEqualTo(wrapper.Record, anyTagEqualToFilter);

                    if (result == false)
                    {
                        break;
                    }
                }
                else
                {
                    throw new InvalidOperationException($"Unsupported filter clause type {clause.GetType().Name}");
                }
            }

            return result;
        });
    }

    /// <summary>
    /// Check if the required property on the record is equal to the required value form the filter.
    /// </summary>
    /// <param name="record">The record to check against the filter.</param>
    /// <param name="equalToFilter">The filter containing the property and value to check.</param>
    /// <returns><see langword="true"/> if the property equals the required value, <see langword="false"/> otherwise.</returns>
    private static bool CheckEqualTo(object record, EqualToFilterClause equalToFilter)
    {
        var propertyInfo = GetPropertyInfo(record, equalToFilter.FieldName);
        var propertyValue = propertyInfo.GetValue(record);
        if (propertyValue == null)
        {
            return propertyValue == equalToFilter.Value;
        }

        return propertyValue.Equals(equalToFilter.Value);
    }

    /// <summary>
    /// Check if the required tag list on the record is equal to the required value form the filter.
    /// </summary>
    /// <param name="record">The record to check against the filter.</param>
    /// <param name="anyTagEqualToFilter">The filter containing the property and value to check.</param>
    /// <returns><see langword="true"/> if the tag list contains the required value, <see langword="false"/> otherwise.</returns>
    /// <exception cref="InvalidOperationException"></exception>
    private static bool CheckAnyTagEqualTo(object record, AnyTagEqualToFilterClause anyTagEqualToFilter)
    {
        var propertyInfo = GetPropertyInfo(record, anyTagEqualToFilter.FieldName);

        // Check that the property is actually a list of values.
        if (!typeof(IEnumerable).IsAssignableFrom(propertyInfo.PropertyType))
        {
            throw new InvalidOperationException($"Property {anyTagEqualToFilter.FieldName} is not a list property on record type {record.GetType().Name}");
        }

        // Check that the tag list contains any values. If not, return false, since the required value cannot be in an empty list.
        var propertyValue = propertyInfo.GetValue(record) as IEnumerable;
        if (propertyValue == null)
        {
            return false;
        }

        // Check each value in the tag list against the required value.
        foreach (var value in propertyValue)
        {
            if (value == null && anyTagEqualToFilter.Value == null)
            {
                return true;
            }

            if (value != null && value.Equals(anyTagEqualToFilter.Value))
            {
                return true;
            }
        }

        return false;
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    /// <summary>
    /// Get the property info for the provided property name on the record.
    /// </summary>
    /// <param name="record">The record to find the property on.</param>
    /// <param name="propertyName">The name of the property to find.</param>
    /// <returns>The property info for the required property.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the required property does not exist on the record.</exception>
    private static PropertyInfo GetPropertyInfo(object record, string propertyName)
    {
        var propertyInfo = record.GetType().GetProperty(propertyName);
        if (propertyInfo == null)
        {
            throw new InvalidOperationException($"Property {propertyName} not found on record type {record.GetType().Name}");
        }

        return propertyInfo;
    }
}
