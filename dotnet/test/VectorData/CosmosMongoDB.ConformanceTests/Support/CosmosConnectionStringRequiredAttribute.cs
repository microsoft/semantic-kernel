// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Xunit;

namespace CosmosMongoDB.ConformanceTests.Support;

/// <summary>
/// Checks whether the sqlite_vec extension is properly installed, and skips the test(s) otherwise.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class CosmosConnectionStringRequiredAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync() => new(CosmosMongoTestEnvironment.IsConnectionStringDefined);

    public string Skip { get; set; } = "The Cosmos connection string hasn't been configured (CosmosMongo:ConnectionString).";

    public string SkipReason
        => this.Skip;
}
