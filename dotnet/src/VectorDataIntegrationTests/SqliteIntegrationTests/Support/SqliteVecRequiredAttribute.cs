// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Xunit;

namespace SqliteIntegrationTests.Support;

/// <summary>
/// Checks whether the sqlite_vec extension is properly installed, and skips the test(s) otherwise.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class SqliteVecRequiredAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync() => new(SqliteTestEnvironment.IsSqliteVecInstalled);

    public string Skip { get; set; } = "The sqlite_vec extension is not installed.";

    public string SkipReason
        => this.Skip;
}
