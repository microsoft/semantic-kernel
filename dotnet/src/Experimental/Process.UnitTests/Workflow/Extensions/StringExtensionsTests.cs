// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Extensions;

public class StringExtensionsTests
{
    [Fact]
    public void TrimJsonWithDelimeter()
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
        string result = input.TrimJsonDelimeter();

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
        string result = input.TrimJsonDelimeter();

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
    public void TrimJsonWithUnqualifiedDelimeter()
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
        string result = input.TrimJsonDelimeter();

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
    public void TrimJsonWithoutDelimeter()
    {
        // Arrange
        const string input =
            """
            {
                "key": "value"
            }
            """;

        // Act
        string result = input.TrimJsonDelimeter();

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
    public void TrimJsonWithoutDelimeterWithPadding()
    {
        // Arrange
        const string input =
            """

            {
                "key": "value"
            }    
            """;

        // Act
        string result = input.TrimJsonDelimeter();

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
    public void TrimMissingWithDelimeter()
    {
        // Arrange
        const string input =
            """
            ```json
            ```
            """;

        // Act
        string result = input.TrimJsonDelimeter();

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void TrimEmptyString()
    {
        // Act
        string result = string.Empty.TrimJsonDelimeter();

        // Assert
        Assert.Equal(string.Empty, result);
    }
}
