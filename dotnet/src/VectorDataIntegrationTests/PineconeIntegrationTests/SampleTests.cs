// Copyright (c) Microsoft. All rights reserved.

using Pinecone;
using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace PineconeIntegrationTests;

public class SampleTests(PineconeFixture fixture) : IClassFixture<PineconeFixture>
{
    [ConditionalFact]
    public async Task CanRunSampleCode()
    {
        const string IndexName = "sample-index-name";

        await fixture.Client.CreateIndexAsync(new CreateIndexRequest
        {
            Name = IndexName,
            Dimension = 2,
            Metric = CreateIndexRequestMetric.Cosine,
            Spec = new ServerlessIndexSpec
            {
                Serverless = new ServerlessSpec
                {
                    Cloud = ServerlessSpecCloud.Aws,
                    Region = "us-east-1",
                }
            },
            DeletionProtection = DeletionProtection.Disabled,
        });

        await fixture.Client.DeleteIndexAsync(IndexName);
    }
}
