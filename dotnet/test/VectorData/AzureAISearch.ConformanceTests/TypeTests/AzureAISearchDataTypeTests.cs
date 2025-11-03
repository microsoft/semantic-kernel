// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace AzureAISearch.ConformanceTests.TypeTests;

public class AzureAISearchDataTypeTests(AzureAISearchDataTypeTests.Fixture fixture)
    : DataTypeTests<string, AzureAISearchDataTypeTests.Fixture.AzureAISearchRecord>(fixture),
    IClassFixture<AzureAISearchDataTypeTests.Fixture>
{
    public override Task Byte() => Task.CompletedTask;
    public override Task Short() => Task.CompletedTask;
    public override Task Decimal() => Task.CompletedTask;

    [ConditionalFact(Skip = "Guid not yet supported")]
    public override Task Guid() => Task.CompletedTask;

    [ConditionalFact(Skip = "DateTime not yet supported")]
    public override Task DateTime() => Task.CompletedTask;

    // [ConditionalFact(Skip = "DateTimeOffset not yet supported")]
    // public override Task DateTimeOffset() => Task.CompletedTask;

    [ConditionalFact(Skip = "DateOnly not yet supported")]
    public override Task DateOnly() => Task.CompletedTask;

    [ConditionalFact(Skip = "TimeOnly not yet supported")]
    public override Task TimeOnly() => Task.CompletedTask;

    public override Task String_array() => Task.CompletedTask;

    protected override object? GenerateEmptyProperty(VectorStoreProperty property)
        => property.Type switch
        {
            null => throw new InvalidOperationException($"Property '{property.Name}' has no type defined."),

            // In Azure AI Search, array fields must be non-null (at least for now)
            var t when t.IsArray => Array.CreateInstance(t.GetElementType()!, 0),

            _ => base.GenerateEmptyProperty(property)
        };

    public new class Fixture : DataTypeTests<string, Fixture.AzureAISearchRecord>.Fixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "data-type-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override IList<VectorStoreDataProperty> GetDataProperties()
            => base.GetDataProperties().Where(p =>
                p.Type != typeof(byte)
                && p.Type != typeof(short)
                && p.Type != typeof(decimal)
                && p.Type != typeof(Guid)
                && p.Type != typeof(DateTime)
#if NET8_0_OR_GREATER
                && p.Type != typeof(DateOnly)
                && p.Type != typeof(TimeOnly)
#endif
            ).ToList();

        public class AzureAISearchRecord : RecordBase
        {
            public int Int { get; set; }
            public long Long { get; set; }
            public float Float { get; set; }
            public double Double { get; set; }

            public string? String { get; set; }
            public bool Bool { get; set; }

            public DateTimeOffset DateTimeOffset { get; set; }

            public string[] StringArray { get; set; } = null!;

            public int? NullableInt { get; set; }
        }
    }
}
