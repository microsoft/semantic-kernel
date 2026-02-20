// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Xunit;

namespace SemanticKernel.Connectors.PgVector.UnitTests;

public sealed class PostgresFilterTranslatorTests
{
    [Fact]
    public void DateTime_Utc_FormattedWithZ()
    {
        // Inline new DateTime(..., DateTimeKind.Utc) in expression tree to exercise TranslateConstant
        var sql = TranslateFilter<TestRecord>(r => r.Created == new DateTime(2024, 6, 15, 10, 30, 45, DateTimeKind.Utc));
        Assert.Contains("'2024-06-15T10:30:45Z'", sql);
    }

    [Fact]
    public void DateTime_Unspecified_FormattedWithoutZ()
    {
        // Inline new DateTime(...) has Kind=Unspecified
        var sql = TranslateFilter<TestRecord>(r => r.Created == new DateTime(2024, 6, 15, 10, 30, 45));
        Assert.Contains("'2024-06-15T10:30:45'", sql);
        Assert.DoesNotContain("Z'", sql);
    }

    [Fact]
    public void DateTimeOffset_Utc_FormattedWithZ()
    {
        // Use a ConstantExpression directly to bypass VisitNew issues with TimeSpan.Zero
        var sql = TranslateFilterWithConstant<TestRecord, DateTimeOffset>(
            nameof(TestRecord.CreatedOffset),
            new DateTimeOffset(2024, 6, 15, 10, 30, 45, TimeSpan.Zero));
        Assert.Contains("'2024-06-15T10:30:45Z'", sql);
    }

    [Fact]
    public void DateTimeOffset_NonZeroOffset_Throws()
    {
        Assert.ThrowsAny<NotSupportedException>(() =>
            TranslateFilterWithConstant<TestRecord, DateTimeOffset>(
                nameof(TestRecord.CreatedOffset),
                new DateTimeOffset(2024, 6, 15, 10, 30, 45, TimeSpan.FromHours(2))));
    }

    private static string TranslateFilter<TRecord>(Expression<Func<TRecord, bool>> filter)
    {
        var model = BuildModel();
        var sb = new StringBuilder();
        var translator = new PostgresFilterTranslator(model, filter, startParamIndex: 1, sb);
        translator.Translate(appendWhere: false);
        return sb.ToString();
    }

    private static string TranslateFilterWithConstant<TRecord, TValue>(string propertyName, TValue value)
    {
        var model = BuildModel();
        var param = Expression.Parameter(typeof(TRecord), "r");
        var prop = Expression.Property(param, propertyName);
        var constant = Expression.Constant(value, typeof(TValue));
        var body = Expression.Equal(prop, constant);
        var filter = Expression.Lambda<Func<TRecord, bool>>(body, param);

        var sb = new StringBuilder();
        var translator = new PostgresFilterTranslator(model, filter, startParamIndex: 1, sb);
        translator.Translate(appendWhere: false);
        return sb.ToString();
    }

    private static CollectionModel BuildModel()
    {
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("Id", typeof(Guid)),
                new VectorStoreDataProperty("Created", typeof(DateTime)),
                new VectorStoreDataProperty("CreatedOffset", typeof(DateTimeOffset)),
                new VectorStoreVectorProperty("Embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        return new PostgresModelBuilder().BuildDynamic(definition, defaultEmbeddingGenerator: null);
    }

#pragma warning disable CA1812 // internal class that is apparently never instantiated.
    private sealed record TestRecord
    {
        public Guid Id { get; set; }
        public DateTime Created { get; set; }
        public DateTimeOffset CreatedOffset { get; set; }
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812
}
