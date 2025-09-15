// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Xunit;

namespace SqliteVec.ConformanceTests.Support;

/// <summary>
/// Checks whether the sqlite_vec extension is properly installed, and skips the test(s) otherwise.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class SqliteVecRequiredAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync() => new(SqliteTestEnvironment.CanUseSqlite);

    public string Skip { get; set; } = "Some native Sqlite dependencies are missing.";

    public string SkipReason
        => this.Skip;
}
