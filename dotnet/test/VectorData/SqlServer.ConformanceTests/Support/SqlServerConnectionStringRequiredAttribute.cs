// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Xunit;

namespace SqlServer.ConformanceTests.Support;

/// <summary>
/// Checks whether the connection string for Sql Server is provided, and skips the test(s) otherwise.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class SqlServerConnectionStringRequiredAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync() => new(SqlServerTestEnvironment.IsConnectionStringDefined);

    public string Skip { get; set; } = "ConnectionString is not configured, set SqlServer:ConnectionString.";

    public string SkipReason => this.Skip;
}
