// Copyright (c) Microsoft. All rights reserved.

namespace VectorDataSpecificationTests.Xunit;

/// <summary>
/// Disable the tests in the decorated scope.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class DisableTestsAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync()
    {
        return new(false);
    }

    public string Skip { get; set; } = "Test disabled due to usage of DisableTestsAttribute";

    public string SkipReason
        => this.Skip;
}
