// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

public class PineconeFactDiscoverer(IMessageSink messageSink) : FactDiscoverer(messageSink)
{
    protected override IXunitTestCase CreateTestCase(
        ITestFrameworkDiscoveryOptions discoveryOptions,
        ITestMethod testMethod,
        IAttributeInfo factAttribute)
        => new PineconeFactTestCase(
            this.DiagnosticMessageSink,
            discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(),
            testMethod);
}
