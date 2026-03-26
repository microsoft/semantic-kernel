// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Extension methods for configuring PostgreSQL-specific properties on vector store property definitions.
/// </summary>
public static class PostgresPropertyExtensions
{
    private const string FullTextSearchLanguageKey = "Postgres:FullTextSearchLanguage";
    private const string StoreTypeKey = "Postgres:StoreType";

    #region Full-text search language

    /// <summary>
    /// Sets the PostgreSQL full-text search language for a data property.
    /// </summary>
    /// <param name="property">The data property to configure.</param>
    /// <param name="language">The PostgreSQL text search language name (e.g., "english", "spanish", "german").</param>
    /// <returns>The same property instance for method chaining.</returns>
    /// <remarks>
    /// This language is used with PostgreSQL's <c>to_tsvector</c> and <c>plainto_tsquery</c> functions
    /// when creating GIN indexes and performing full-text search operations.
    /// Common language options include: "simple", "english", "spanish", "german", "french", etc.
    /// See PostgreSQL documentation for the full list of available text search configurations.
    /// </remarks>
    public static VectorStoreDataProperty WithFullTextSearchLanguage(this VectorStoreDataProperty property, string? language)
    {
        property.ProviderAnnotations ??= [];
        property.ProviderAnnotations[FullTextSearchLanguageKey] = language;
        return property;
    }

    /// <summary>
    /// Gets the PostgreSQL full-text search language configured for a data property.
    /// </summary>
    /// <param name="property">The data property to read from.</param>
    /// <returns>The configured language, or <see langword="null"/> if not set.</returns>
    public static string? GetFullTextSearchLanguage(this VectorStoreDataProperty property)
        => property.ProviderAnnotations?.TryGetValue(FullTextSearchLanguageKey, out var value) == true
            ? value as string
            : null;

    /// <summary>
    /// Gets the PostgreSQL full-text search language configured for a data property model.
    /// </summary>
    /// <param name="property">The data property model to read from.</param>
    /// <returns>The configured language, or the default language ("english") if not set.</returns>
    internal static string GetFullTextSearchLanguageOrDefault(this DataPropertyModel property)
        => property.ProviderAnnotations?.TryGetValue(FullTextSearchLanguageKey, out var value) == true && value is string language
            ? language
            : PostgresConstants.DefaultFullTextSearchLanguage;

    #endregion Full-text search language

    #region Store type

    /// <summary>
    /// Sets the PostgreSQL store type for a property, overriding the default type mapping.
    /// </summary>
    /// <param name="property">The property to configure.</param>
    /// <param name="storeType">
    /// The PostgreSQL type name. Currently, only <c>"timestamp"</c> and <c>"timestamp without time zone"</c>
    /// are supported, and only on <see cref="DateTime"/> properties. This causes the property to be stored as
    /// PostgreSQL <c>timestamp</c> (without time zone) instead of the default <c>timestamptz</c>.
    /// </param>
    /// <returns>The same property instance for method chaining.</returns>
    /// <remarks>
    /// <para>
    /// By default, .NET <see cref="DateTime"/> properties are mapped to PostgreSQL <c>timestamptz</c> (timestamp with time zone),
    /// which requires UTC values. Use this method to map to <c>timestamp</c> (without time zone) instead, which stores
    /// local/unspecified date-time values without time zone information.
    /// </para>
    /// <para>
    /// When using <c>timestamp</c>, <see cref="DateTime"/> values with <see cref="DateTimeKind.Unspecified"/> or
    /// <see cref="DateTimeKind.Local"/> kind should be used. Values read back from the database will have
    /// <see cref="DateTimeKind.Unspecified"/>.
    /// </para>
    /// </remarks>
    /// <exception cref="NotSupportedException">Thrown if the <paramref name="storeType"/> is not a supported value.</exception>
    public static TProperty WithStoreType<TProperty>(this TProperty property, string storeType)
        where TProperty : VectorStoreProperty
    {
        if (!IsTimestampStoreType(storeType))
        {
            throw new NotSupportedException(
                $"Store type '{storeType}' is not supported. Only 'timestamp' and 'timestamp without time zone' are supported.");
        }

        property.ProviderAnnotations ??= [];
        property.ProviderAnnotations[StoreTypeKey] = storeType;
        return property;
    }

    /// <summary>
    /// Gets the PostgreSQL store type configured for a property.
    /// </summary>
    /// <param name="property">The property to read from.</param>
    /// <returns>The configured store type, or <see langword="null"/> if not set.</returns>
    public static string? GetStoreType(this VectorStoreProperty property)
        => property.ProviderAnnotations?.TryGetValue(StoreTypeKey, out var value) == true
            ? value as string
            : null;

    /// <summary>
    /// Gets whether the property model has been configured with a <c>timestamp</c> (without time zone) store type.
    /// </summary>
    internal static bool IsTimestampWithoutTimezone(this PropertyModel property)
        => property.ProviderAnnotations?.TryGetValue(StoreTypeKey, out var value) == true
            && value is string storeType
            && IsTimestampStoreType(storeType);

    private static bool IsTimestampStoreType(string storeType)
        => string.Equals(storeType, "timestamp", StringComparison.OrdinalIgnoreCase)
            || string.Equals(storeType, "timestamp without time zone", StringComparison.OrdinalIgnoreCase);

    #endregion Store type
}
