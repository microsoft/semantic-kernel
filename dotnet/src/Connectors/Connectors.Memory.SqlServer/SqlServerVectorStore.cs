// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
// TODO adsitnik: design: the interface is not generic, so I am not sure how the users can customize the
// mapping between the record and the table. Am I missing something?
// The interface I am talking about: public IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>.
public sealed class SqlServerVectorStore : IVectorStore, IDisposable
{
    private static readonly ConcurrentDictionary<Type, VectorStoreRecordPropertyReader> s_propertyReaders = new();

    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(int), // INT 
        typeof(long), // BIGINT
        typeof(string), // VARCHAR 
        typeof(Guid), // UNIQUEIDENTIFIER
        // TODO adsitnik: do we want to support DATETIME (DateTime) and VARBINARY (byte[])?
    ];

    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(int), // INT
        typeof(long), // BIGINT.
        typeof(Guid), // UNIQUEIDENTIFIER.
        typeof(string), // NVARCHAR
        typeof(byte[]), //VARBINARY
        typeof(bool), // BIT
        typeof(DateTime), // DATETIME
        typeof(TimeSpan), // TIME
        typeof(decimal), // DECIMAL
        typeof(double), // FLOAT
        typeof(float) // REAL
    ];

    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>), // VECTOR
        typeof(ReadOnlyMemory<float>?)
    ];

    private readonly SqlConnection _connection;
    private readonly SqlServerVectorStoreOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStore"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="options">Optional configuration options.</param>
    public SqlServerVectorStore(SqlConnection connection, SqlServerVectorStoreOptions? options = null)
    {
        // TODO adsitnik: design:
        // Do we need a ctor that takes the connection string and creates a connection?
        // What is the story with pooling for the SqlConnection type?
        // Does it maintain a private instance pool? Or a static one?
        this._connection = connection;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = options is not null
            ? new() { Schema = options.Schema, EmbeddingDimensionsCount = options.EmbeddingDimensionsCount }
            : SqlServerVectorStoreOptions.Defaults;
    }

    /// <inheritdoc/>
    public void Dispose() => this._connection.Dispose();

    // TODO: adsitnik: design
    // I find the creation process not intuitive: the IVectorStoreRecordCollection.Create
    // method does take only table name as an arugment, the metadata needs to be provided
    // a step before that by passing the VectorStoreRecordDefinition to the GetCollection method.
    // I would expect VectorStoreRecordDefinition to be argument of the CreateCollectionAsync.
    // Also, please consider another problem:
    // On Monday, I pass two arguments to GetCollection:
    // a name: "theName"
    // and a definition: "theDefinition" that consists of two properties
    // When I call CreateCollectionAsync, it gets created.
    // On Tuesday, I pass the same name, but a different definition: three properties.
    // Now CollectionExistsAsync returns true, despite the properties mismatch?!
    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        Verify.NotNull(name);

        if (!s_propertyReaders.TryGetValue(typeof(TRecord), out VectorStoreRecordPropertyReader? propertyReader))
        {
            propertyReader = new(typeof(TRecord),
                // TODO adsitnik: should we cache the property reader when user has provided the VectorStoreRecordDefinition?
                vectorStoreRecordDefinition,
                new()
                {
                    RequiresAtLeastOneVector = false,
                    // TODO adsitnik: design: can TKey represent a composite key (PRIMARY KEY)?
                    SupportsMultipleKeys = false,
                    SupportsMultipleVectors = true,
                });

            propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
            // TODO adsitnik: get the list of supported ienumerable types
            propertyReader.VerifyDataProperties(s_supportedDataTypes, supportEnumerable: true);
            propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

            // Add to the cache once we have verified the record definition.
            s_propertyReaders.TryAdd(typeof(TRecord), propertyReader);
        }

        return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(
            this._connection,
            name,
            this._options,
            propertyReader);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqlCommand cmd = SqlServerCommandBuilder.SelectTableNames(this._connection, this._options.Schema);
        using SqlDataReader reader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return reader.GetString(reader.GetOrdinal("table_name"));
        }
    }
}
