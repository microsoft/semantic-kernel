// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Linq.Expressions;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

#pragma warning disable MEVD9001 // Experimental

public sealed class RedisFilterTranslatorTests
{
    [Fact]
    public void Contains_with_simple_string()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo"));
        Assert.Equal("""@Tags:{"foo"}""", result);
    }

    [Fact]
    public void Contains_with_curly_brace_in_value()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo}bar"));
        Assert.Equal("""@Tags:{"foo}bar"}""", result);
    }

    [Fact]
    public void Contains_with_pipe_in_value()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo|bar"));
        Assert.Equal("""@Tags:{"foo|bar"}""", result);
    }

    [Fact]
    public void Contains_with_double_quote_in_value()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo\"bar"));
        Assert.Equal("""@Tags:{"foo\"bar"}""", result);
    }

    [Fact]
    public void Contains_with_asterisk_in_value()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo*bar"));
        Assert.Equal("""@Tags:{"foo*bar"}""", result);
    }

    [Fact]
    public void Contains_with_at_sign_in_value()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("foo@bar"));
        Assert.Equal("""@Tags:{"foo@bar"}""", result);
    }

    [Fact]
    public void Contains_with_injection_attempt()
    {
        var result = Translate<TestRecord>(r => r.Tags.Contains("evil} | @secret:{*"));
        Assert.Equal("""@Tags:{"evil} | @secret:{*"}""", result);
    }

    [Fact]
    public void Any_with_simple_strings()
    {
        var values = new[] { "a", "b" };
        var result = Translate<TestRecord>(r => r.Tags.Any(t => values.Contains(t)));
        Assert.Equal("""@Tags:{"a" | "b"}""", result);
    }

    [Fact]
    public void Any_with_metacharacters_in_values()
    {
        var values = new[] { "a|b", "c}d" };
        var result = Translate<TestRecord>(r => r.Tags.Any(t => values.Contains(t)));
        Assert.Equal("""@Tags:{"a|b" | "c}d"}""", result);
    }

    [Fact]
    public void Any_with_double_quotes_in_values()
    {
        var values = new[] { "a\"b", "c\"d" };
        var result = Translate<TestRecord>(r => r.Tags.Any(t => values.Contains(t)));
        Assert.Equal("""@Tags:{"a\"b" | "c\"d"}""", result);
    }

    [Fact]
    public void Any_with_injection_attempt()
    {
        var values = new[] { "safe", "x} | @admin:{true" };
        var result = Translate<TestRecord>(r => r.Tags.Any(t => values.Contains(t)));
        Assert.Equal("""@Tags:{"safe" | "x} | @admin:{true"}""", result);
    }

    [Fact]
    public void Equal_with_simple_string()
    {
        var result = Translate<TestRecord>(r => r.Name == "foo");
        Assert.Equal("""@Name:{"foo"}""", result);
    }

    [Fact]
    public void Equal_with_double_quote_in_value()
    {
        var result = Translate<TestRecord>(r => r.Name == "foo\"bar");
        Assert.Equal("""@Name:{"foo\"bar"}""", result);
    }

    private static string Translate<TRecord>(Expression<Func<TRecord, bool>> filter)
    {
        var model = BuildModel();
        return new RedisFilterTranslator().Translate(filter, model);
    }

    private static CollectionModel BuildModel()
    {
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("Id", typeof(string)),
                new VectorStoreDataProperty("Name", typeof(string)),
                new VectorStoreDataProperty("Tags", typeof(string[])),
                new VectorStoreVectorProperty("Embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        return new RedisJsonModelBuilder(RedisJsonCollection<string, object>.ModelBuildingOptions).BuildDynamic(definition, defaultEmbeddingGenerator: null);
    }

#pragma warning disable CA1812
    private sealed record TestRecord
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string[] Tags { get; set; } = [];
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812
}
