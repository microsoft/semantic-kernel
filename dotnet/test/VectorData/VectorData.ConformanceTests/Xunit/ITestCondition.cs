// Copyright (c) Microsoft. All rights reserved.

namespace VectorData.ConformanceTests.Xunit;

public interface ITestCondition
{
    ValueTask<bool> IsMetAsync();

    string SkipReason { get; }
}
