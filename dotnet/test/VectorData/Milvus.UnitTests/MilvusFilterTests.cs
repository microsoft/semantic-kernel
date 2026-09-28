// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Milvus;
using Xunit;

namespace SemanticKernel.Connectors.Milvus.UnitTests;

public sealed class MilvusFilterTests
{
    [Theory]
    [InlineData("v2.3.0")]
    [InlineData("v2.3.0-dev")]
    [InlineData("2.3.0")]
    [InlineData("v2.6.1")]
    [InlineData("3.0.0")]
    public void AcceptsSupportedServerVersions(string version)
    {
        MilvusMemoryStore.ValidateServerVersion(version);
    }

    [Theory]
    [InlineData("v2.2.14")]
    [InlineData("v2.2.14-dev")]
    [InlineData("v2.2.16")]
    [InlineData("v2.3.0-beta")]
    [InlineData("unknown")]
    [InlineData("")]
    public void RejectsOlderOrUnrecognizedServerVersions(string version)
    {
        Assert.Throws<NotSupportedException>(() => MilvusMemoryStore.ValidateServerVersion(version));
    }

    [Theory]
    [InlineData("", "")]
    [InlineData("ordinary-id", "ordinary-id")]
    [InlineData("[],'", "[],'")]
    [InlineData("\"", "\\\"")]
    [InlineData("\\", "\\\\")]
    [InlineData("\\\"", "\\\\\\\"")]
    [InlineData("trailing\\", "trailing\\\\")]
    [InlineData("\r\n\t", "\\r\\n\\t")]
    [InlineData("\\r\\n\\t", "\\\\r\\\\n\\\\t")]
    [InlineData("\0\b\f\v\u001f\u007f\u0085", "\\u0000\\u0008\\u000c\\u000b\\u001f\\u007f\\u0085")]
    [InlineData("\u00e9\u4e2d\ud83d\ude00", "\u00e9\u4e2d\ud83d\ude00")]
    [InlineData("a\"] || true || id in [\"", "a\\\"] || true || id in [\\\"")]
    [InlineData("z\"] && text like \"%secret%\" || id in [\"", "z\\\"] && text like \\\"%secret%\\\" || id in [\\\"")]
    [InlineData("x\" || id != \"", "x\\\" || id != \\\"")]
    [InlineData("a\",\"victim", "a\\\",\\\"victim")]
    public void EncodesEachIdAsOneString(string key, string expected)
    {
        Assert.Equal("id in [\"" + expected + "\"]", MilvusMemoryStore.BuildIdFilter([key]));
    }

    [Fact]
    public void PreservesEmptyLists()
    {
        Assert.Equal("id in []", MilvusMemoryStore.BuildIdFilter([]));
    }

    [Fact]
    public void PreservesOrderDuplicatesAndEmptyIds()
    {
        Assert.Equal("id in [\"a\",\"\",\"a\",\"b\"]", MilvusMemoryStore.BuildIdFilter(["a", "", "a", "b"]));
    }

    [Fact]
    public void EnumeratesKeysOnlyOnce()
    {
        bool enumerated = false;

        IEnumerable<string> Keys()
        {
            Assert.False(enumerated);
            enumerated = true;
            yield return "first";
            yield return "second";
        }

        Assert.Equal("id in [\"first\",\"second\"]", MilvusMemoryStore.BuildIdFilter(Keys()));
        Assert.True(enumerated);
    }
}
