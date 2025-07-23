// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Extensions;

public class StringExtensionsTests
{
    [Fact]
    public void TrimJsonWithDelimiter()
    {
        // Arrange
        const string input =
            """
            ```json
            {
                "key": "value"
            }
            ```
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(
            """
            {
                "key": "value"
            }
            """,
            result);
    }
    [Fact]
    public void TrimJsonWithPadding()
    {
        // Arrange
        const string input =
            """
                 
            ```json
            {
                "key": "value"
            }
            ```       
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(
            """
            {
                "key": "value"
            }
            """,
            result);
    }

    [Fact]
    public void TrimJsonWithUnqualifiedDelimiter()
    {
        // Arrange
        const string input =
            """
            ```
            {
                "key": "value"
            }
            ```
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(
            """
            {
                "key": "value"
            }
            """,
            result);
    }

    [Fact]
    public void TrimJsonWithoutDelimiter()
    {
        // Arrange
        const string input =
            """
            {
                "key": "value"
            }
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(
            """
            {
                "key": "value"
            }
            """,
            result);
    }

    [Fact]
    public void TrimJsonWithoutDelimiterWithPadding()
    {
        // Arrange
        const string input =
            """

            {
                "key": "value"
            }    
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(
            """
            {
                "key": "value"
            }
            """,
            result);
    }

    [Fact]
    public void TrimMissingWithDelimiter()
    {
        // Arrange
        const string input =
            """
            ```json
            ```
            """;

        // Act
        string result = input.TrimJsonDelimiter();

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void TrimEmptyString()
    {
        // Act
        string result = string.Empty.TrimJsonDelimiter();

        // Assert
        Assert.Equal(string.Empty, result);
    }
}
