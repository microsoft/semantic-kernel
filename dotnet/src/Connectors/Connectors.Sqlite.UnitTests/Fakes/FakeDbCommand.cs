// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data;
using System.Data.Common;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

#pragma warning disable CS8618, CS8765

internal sealed class FakeDbCommand(
    DbDataReader? dataReader = null,
    DbParameterCollection? parameterCollection = null) : DbCommand
{
    public override string CommandText { get; set; }
    public override int CommandTimeout { get; set; }
    public override CommandType CommandType { get; set; }
    public override bool DesignTimeVisible { get; set; }
    public override UpdateRowSource UpdatedRowSource { get; set; }
    protected override DbConnection? DbConnection { get; set; }

    protected override DbParameterCollection DbParameterCollection => parameterCollection ?? throw new NotImplementedException();

    protected override DbTransaction? DbTransaction { get; set; }

    public override void Cancel()
    {
        throw new NotImplementedException();
    }

    public override int ExecuteNonQuery()
    {
        throw new NotImplementedException();
    }

    public override object? ExecuteScalar()
    {
        throw new NotImplementedException();
    }

    public override void Prepare()
    {
        throw new NotImplementedException();
    }

    protected override DbParameter CreateDbParameter()
    {
        throw new NotImplementedException();
    }

    protected override DbDataReader ExecuteDbDataReader(CommandBehavior behavior) => dataReader ?? throw new NotImplementedException();
}
