// Copyright (c) Microsoft. All rights reserved.

using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.PowerFx;

/// <summary>
/// Base test class for PowerFx engine tests.
/// </summary>
public abstract class RecalcEngineTest(ITestOutputHelper output) : WorkflowTest(output)
{
    internal ProcessActionScopes Scopes { get; } = new();

    protected RecalcEngine CreateEngine(int maximumExpressionLength = 100) => RecalcEngineFactory.Create(this.Scopes, maximumExpressionLength);
}
