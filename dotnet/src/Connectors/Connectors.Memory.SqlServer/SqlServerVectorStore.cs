// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="VectorStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
public sealed class SqlServerVectorStore : VectorStore
{
    private readonly string _connectionString;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>The database schema.</summary>
    private readonly string? _schema;

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Optional configuration options.</param>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public SqlServerVectorStore(string connectionString, SqlServerVectorStoreOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        this._connectionString = connectionString;

        options ??= SqlServerVectorStoreOptions.Defaults;
        this._schema = options.Schema;
        this._embeddingGenerator = options.EmbeddingGenerator;

        var connectionStringBuilder = new SqlConnectionStringBuilder(connectionString);

        this._metadata = new()
        {
            VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.InitialCatalog
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc/>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
#if NET8_0_OR_GREATER
    public override SqlServerCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new SqlServerCollection<TKey, TRecord>(
                this._connectionString,
                name,
                new()
                {
                    Schema = this._schema,
                    Definition = definition,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
#if NET8_0_OR_GREATER
    public override SqlServerDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new SqlServerDynamicCollection(
            this._connectionString,
            name,
            new()
            {
                Schema = this._schema,
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator,
            }
        );
#pragma warning restore IDE0090

    /// <inheritdoc/>
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableNames(connection, this._schema);

        using SqlDataReader reader = await connection.ExecuteWithErrorHandlingAsync(
            this._metadata,
            operationName: "ListCollectionNames",
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        while (await reader.ReadWithErrorHandlingAsync(
            this._metadata,
            operationName: "ListCollectionNames",
            cancellationToken).ConfigureAwait(false))
        {
            yield return reader.GetString(reader.GetOrdinal("table_name"));
        }
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.EnsureCollectionDeletedAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
