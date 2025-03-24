// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using AzureAISearchIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace AzureAISearchIntegrationTests.Filter;

public class AzureAISearchBasicQueryTests(AzureAISearchBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<AzureAISearchBasicQueryTests.Fixture>
{
    protected override async Task<List<FilterRecord>> GetResults(Expression<Func<FilterRecord, bool>> filter, int top)
        // Azure AI Search requires the field to be created as "IsSortable": true.
        // We currently don't expose an API for that (see #11130), so we have to sort the results manually.
        => (await fixture.Collection.QueryAsync(new() { Filter = filter, Top = top }).ToListAsync()).OrderBy(r => r.Key).ToList();

    // Azure AI Search only supports search.in() over strings
    public override Task Contains_over_inline_int_array()
        => Assert.ThrowsAsync<NotSupportedException>(() => base.Contains_over_inline_int_array());

    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        protected override string CollectionName => "query-tests";
    }
}
