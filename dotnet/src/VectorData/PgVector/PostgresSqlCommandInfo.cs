// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Represents a SQL command for Postgres.
/// </summary>
internal class PostgresSqlCommandInfo
{
    /// <summary>
    /// Gets or sets the SQL command text.
    /// </summary>
    public string CommandText { get; set; }
    /// <summary>
    /// Gets or sets the parameters for the SQL command.
    /// </summary>
    public List<NpgsqlParameter>? Parameters { get; set; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresSqlCommandInfo"/> class.
    /// </summary>
    /// <param name="commandText">The SQL command text.</param>
    /// <param name="parameters">The parameters for the SQL command.</param>
    public PostgresSqlCommandInfo(string commandText, List<NpgsqlParameter>? parameters = null)
    {
        this.CommandText = commandText;
        this.Parameters = parameters;
    }

    /// <summary>
    /// Converts this instance to an <see cref="NpgsqlCommand"/>.
    /// </summary>
    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
    public NpgsqlCommand ToNpgsqlCommand(NpgsqlConnection connection, NpgsqlTransaction? transaction = null)
    {
        NpgsqlCommand cmd = connection.CreateCommand();
        if (transaction != null)
        {
            cmd.Transaction = transaction;
        }
        cmd.CommandText = this.CommandText;
        if (this.Parameters != null)
        {
            foreach (var parameter in this.Parameters)
            {
                cmd.Parameters.Add(parameter);
            }
        }
        return cmd;
    }
}
