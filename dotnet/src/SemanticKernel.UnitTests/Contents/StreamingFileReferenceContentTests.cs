// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Text;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

#pragma warning disable SKEXP0110

/// <summary>
/// Unit testing of <see cref="StreamingFileReferenceContent"/>.
/// </summary>
public class StreamingFileReferenceContentTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyStreamingFileReferenceContentInitialState()
    {
        Assert.Throws<ArgumentException>(() => new StreamingFileReferenceContent(string.Empty));
    }
    /// <summary>
    /// Verify usage.
    /// </summary>
    [Fact]
    public void VerifyStreamingFileReferenceContentUsage()
    {
        StreamingFileReferenceContent definition = new(fileId: "testfile");

        Assert.Equal("testfile", definition.FileId);
        Assert.Equal("testfile", definition.ToString());
        Assert.Equal("testfile", Encoding.UTF8.GetString(definition.ToByteArray()));
    }
}
