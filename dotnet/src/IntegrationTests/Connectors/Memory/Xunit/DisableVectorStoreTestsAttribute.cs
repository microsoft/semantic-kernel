// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;

/// <summary>
/// Disable the vector store test in the method or class that this attribute is decorated with.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public sealed class DisableVectorStoreTestsAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync()
    {
        return ValueTask.FromResult(false);
    }

    public string Skip { get; set; } = "Test disabled due to usage of DisableVectorStoreTestsAttribute";

    public string SkipReason
        => this.Skip;
}
