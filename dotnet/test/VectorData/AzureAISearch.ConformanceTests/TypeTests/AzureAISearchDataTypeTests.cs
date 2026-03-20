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
    [ConditionalFact(Skip = "Issues around empty collection initialization")]
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

        public override IList<VectorStoreDataProperty> GetDataProperties()
            => base.GetDataProperties().Where(p =>
                p.Type != typeof(byte)
                && p.Type != typeof(short)
                && p.Type != typeof(decimal)
                && p.Type != typeof(Guid)
#if NET
                && p.Type != typeof(TimeOnly)
#endif
            ).ToList();

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
            typeof(short),
            typeof(decimal),
            typeof(Guid),
#if NET
            typeof(TimeOnly)
#endif
        ];

        public class AzureAISearchRecord : RecordBase
        {
            public int Int { get; set; }
            public long Long { get; set; }
            public float Float { get; set; }
            public double Double { get; set; }

            public string? String { get; set; }
            public bool Bool { get; set; }

            public DateTime DateTime { get; set; }
            public DateTimeOffset DateTimeOffset { get; set; }

#if NET
            public DateOnly DateOnly { get; set; }
#endif

            public string[] StringArray { get; set; } = null!;

            public int? NullableInt { get; set; }
        }
    }
}
