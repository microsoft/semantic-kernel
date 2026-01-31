// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Extension methods for configuring PostgreSQL-specific properties on vector store property definitions.
/// </summary>
public static class PostgresPropertyExtensions
{
    private const string FullTextSearchLanguageKey = "Postgres:FullTextSearchLanguage";

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
}
