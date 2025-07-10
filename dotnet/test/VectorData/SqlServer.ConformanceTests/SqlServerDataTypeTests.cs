﻿// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerDataTypeTests(SqlServerDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<SqlServerDataTypeTests.Fixture>
{
    public new class Fixture : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(DateTimeOffset),
            typeof(string[])
        ];
    }
}
