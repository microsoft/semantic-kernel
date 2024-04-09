// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="FileReferenceContent"/>.
/// </summary>
public class FileReferenceContentTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyFileReferenceContentInitialState()
    {
        FileReferenceContent definition = new();

        Assert.Null(definition.FileId);
    }
    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyFileReferenceContentUsage()
    {
        FileReferenceContent definition = new(fileId: "testfile");

        Assert.Equal("testfile", definition.FileId);
    }
}
