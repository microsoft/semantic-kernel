// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.UnitTests.Http;
public class HttpHeaderConstantTests
{
    [Fact]
    public void ItVerifiesStandardUserAgent()
    {
        // Arrange & Act & Assert
        Assert.Equal("Semantic-Kernel", HttpHeaderConstant.Values.UserAgent);
    }

    [Fact]
    public void ItVerifiesUserAgentSupportsPrefix()
    {
        // Arrange & Act & Assert
        HttpHeaderConstant.Values.SetUserAgentPrefix("Test");
        Assert.Equal("Test-Semantic-Kernel", HttpHeaderConstant.Values.UserAgent);
        HttpHeaderConstant.Values.SetUserAgentPrefix(null);
        Assert.Equal("Semantic-Kernel", HttpHeaderConstant.Values.UserAgent);
    }
}
