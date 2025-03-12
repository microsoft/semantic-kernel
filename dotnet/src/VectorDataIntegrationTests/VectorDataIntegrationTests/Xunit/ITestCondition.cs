// Copyright (c) Microsoft. All rights reserved.

namespace VectorDataSpecificationTests.Xunit;

public interface ITestCondition
{
    ValueTask<bool> IsMetAsync();

    string SkipReason { get; }
}
