// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public class SessionsPythonCodeExecutionResultTests
{
    [Fact]
    public void ItShouldConvertResultToString()
    {
        // Arrange
        var result = new SessionsPythonCodeExecutionResult
        {
            Status = "Succeeded",
            Result = new SessionsPythonCodeExecutionResult.ExecutionDetails
            {
                StdOut = "Hello World",
                StdErr = "Error",
                ExecutionResult = "42"
            }
        };

        // Act
        string resultString = result.ToString();

        // Assert
        Assert.Contains("Status: Succeeded", resultString);
        Assert.Contains("Result: 42", resultString);
        Assert.Contains("Stdout: Hello World", resultString);
        Assert.Contains("Stderr: Error", resultString);
    }
}
