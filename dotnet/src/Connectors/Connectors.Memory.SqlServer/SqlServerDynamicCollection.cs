// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Represents a collection of vector store records in a SqlServer database, mapped to a dynamic <c>Dictionary&lt;string, object?&gt;</c>.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class SqlServerDynamicCollection : SqlServerCollection<object, Dictionary<string, object?>>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerDynamicCollection"/> class.
    /// </summary>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public SqlServerDynamicCollection(string connectionString, string name, SqlServerCollectionOptions options)
        : base(
            connectionString,
            name,
            static options => new SqlServerModelBuilder()
                .BuildDynamic(
                    options.Definition ?? throw new ArgumentException("RecordDefinition is required for dynamic collections"),
                    options.EmbeddingGenerator),
            options)
    {
    }
}
