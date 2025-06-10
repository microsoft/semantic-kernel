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
        Assert.Equal("{\"status\":\"Succeeded\",\"result\":\"42\",\"stdOut\":\"Hello World\",\"stdErr\":\"Error\"}", resultString);
    }
}
