// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

#pragma warning disable SKEXP0110

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

        Assert.Empty(definition.FileId);
    }

    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyFileReferenceContentUsage()
    {
        FileReferenceContent definition = new(fileId: "testfile");

        Assert.Equal("testfile", definition.FileId);
        Assert.Null(definition.Tools);
    }

    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyFileReferenceToolUsage()
    {
        FileReferenceContent definition = new(fileId: "testfile") { Tools = new[] { "a", "b", "c" } };

        Assert.Equal("testfile", definition.FileId);
        Assert.NotNull(definition.Tools);
        Assert.Equal(3, definition.Tools.Count);
        Assert.Equivalent(new[] { "a", "b", "c" }, definition.Tools);
    }
}
