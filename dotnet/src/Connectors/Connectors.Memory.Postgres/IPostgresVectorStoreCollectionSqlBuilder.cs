// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Interface for constructing SQL commands for Postgres vector store collections.
/// </summary>
public interface IPostgresVectorStoreCollectionSqlBuilder
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
    /// <param name="recordDefinition">The record definition of the table.</param>
    /// <param name="ifNotExists">Specifies whether to include IF NOT EXISTS in the command.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildCreateTableCommand(string schema, string tableName, VectorStoreRecordDefinition recordDefinition, bool ifNotExists = true);

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
    /// <param name="row">The row to upsert.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, Dictionary<string, object?> row, string keyColumn);

    /// <summary>
    /// Builds a SQL command to get a record from the Postgres vector store.
    /// </summary>
    /// <param name="schema">The schema of the table.</param>
    /// <param name="tableName">The name of the table.</param>
    /// <param name="recordDefinition">The record definition of the table.</param>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="includeVectors">Specifies whether to include vectors in the record.</param>
    /// <returns>The built SQL command info.</returns>
    PostgresSqlCommandInfo BuildGetCommand<TKey>(string schema, string tableName, VectorStoreRecordDefinition recordDefinition, TKey key, bool includeVectors = false) where TKey : notnull;
}