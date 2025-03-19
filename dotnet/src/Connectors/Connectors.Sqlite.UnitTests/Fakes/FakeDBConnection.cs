// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data;
using System.Data.Common;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

#pragma warning disable CS8618, CS8765

internal sealed class FakeDBConnection(DbCommand command) : DbConnection
{
    public override string ConnectionString { get; set; }

    public override string Database => "TestDatabase";

    public override string DataSource => throw new NotImplementedException();

    public override string ServerVersion => throw new NotImplementedException();

    public override ConnectionState State => throw new NotImplementedException();

    public override void ChangeDatabase(string databaseName) => throw new NotImplementedException();

    public override void Close() => throw new NotImplementedException();

    public override void Open() => throw new NotImplementedException();

    protected override DbTransaction BeginDbTransaction(IsolationLevel isolationLevel) => throw new NotImplementedException();

    protected override DbCommand CreateDbCommand() => command;
}
