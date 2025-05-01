// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Interface for constructing SQL commands for Postgres vector store collections.
/// </summary>
internal interface IPostgresVectorStoreCollectionSqlBuilder
{
    /// <summary>
    /// Builds a SQL command to check if a table exists in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <returns>The built SQL command.</returns>
    /// <remarks>
    /// The command must return a single row with a single column named "table_name" if the table exists.
    /// </remarks>
    PostgresSqlCommandInfo BuildDoesTableExistCommand(string schema, string tableName);

    /// <summary>
    /// Builds a SQL command to fetch all tables in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the tables.</param>
    PostgresSqlCommandInfo BuildGetTablesCommand(string schema);

    /// <summary>
    /// Builds a SQL command to create a table in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="ifNotExists">Specifies whether to include IF NOT EXISTS in the command.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildCreateTableCommand(string schema, string tableName, VectorStoreRecordModel model, bool ifNotExists = true);

    /// <summary>
    /// Builds a SQL command to create a vector index in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="columnName">The name of the column.</param>
    /// <param name="indexKind">The kind of index to create.</param>
    /// <param name="distanceFunction">The distance function to use for the index.</param>
    /// <param name="isVector">Specifies whether the column is a vector column.</param>
    /// <param name="ifNotExists">Specifies whether to include IF NOT EXISTS in the command.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildCreateIndexCommand(string schema, string tableName, string columnName, string indexKind, string distanceFunction, bool isVector, bool ifNotExists);

    /// <summary>
    /// Builds a SQL command to drop a table in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildDropTableCommand(string schema, string tableName);

    /// <summary>
    /// Builds a SQL command to upsert a record in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="row">The row to upsert.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, string keyColumn, Dictionary<string, object?> row);

    /// <summary>
    /// Builds a SQL command to upsert a batch of records in the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="rows">The rows to upsert.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildUpsertBatchCommand(string schema, string tableName, string keyColumn, List<Dictionary<string, object?>> rows);

    /// <summary>
    /// Builds a SQL command to get a record from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="includeVectors">Specifies whether to include vectors in the record.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildGetCommand<TKey>(string schema, string tableName, VectorStoreRecordModel model, TKey key, bool includeVectors = false) where TKey : notnull;

    /// <summary>
    /// Builds a SQL command to get a batch of records from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="keys">The keys of the records to get.</param>
    /// <param name="includeVectors">Specifies whether to include vectors in the records.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildGetBatchCommand<TKey>(string schema, string tableName, VectorStoreRecordModel model, List<TKey> keys, bool includeVectors = false) where TKey : notnull;

    /// <summary>
    /// Builds a SQL command to delete a record from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="key">The key of the record to delete.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildDeleteCommand<TKey>(string schema, string tableName, string keyColumn, TKey key);

    /// <summary>
    /// Builds a SQL command to delete a batch of records from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="keys">The keys of the records to delete.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildDeleteBatchCommand<TKey>(string schema, string tableName, string keyColumn, List<TKey> keys);

    /// <summary>
    /// Builds a SQL command to get the nearest match from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="vectorProperty">The property which the vectors to compare are stored in.</param>
    /// <param name="vectorValue">The vector to match.</param>
    /// <param name="legacyFilter">The filter conditions for the query.</param>
    /// <param name="newFilter">The filter conditions for the query.</param>
    /// <param name="skip">The number of records to skip.</param>
    /// <param name="includeVectors">Specifies whether to include vectors in the result.</param>
    /// <param name="limit">The maximum number of records to return.</param>
    /// <returns>The built SQL command info.</returns>
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    PostgresSqlCommandInfo BuildGetNearestMatchCommand<TRecord>(string schema, string tableName, VectorStoreRecordModel model, VectorStoreRecordVectorPropertyModel vectorProperty, Vector vectorValue, VectorSearchFilter? legacyFilter, Expression<Func<TRecord, bool>>? newFilter, int? skip, bool includeVectors, int limit);
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
}
