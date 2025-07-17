// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Process.Workflows;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

/// <summary>
/// Base class for workflow tests.
/// </summary>
public abstract class WorkflowTest : IDisposable
{
    public TestOutputAdapter Output { get; }

    protected WorkflowTest(ITestOutputHelper output)
    {
        this.Output = new TestOutputAdapter(output);
        System.Console.SetOut(this.Output);
    }

    public void Dispose()
    {
        this.Output.Dispose();
        GC.SuppressFinalize(this);
    }

    internal static string FormatVariablePath(string variableName, ActionScopeType? scope = null) => $"{scope ?? ActionScopeType.Topic}.{variableName}";
}
