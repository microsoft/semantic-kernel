// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

public class PineconeTheoryDiscoverer(IMessageSink messageSink) : TheoryDiscoverer(messageSink)
{
    protected override IEnumerable<IXunitTestCase> CreateTestCasesForTheory(
        ITestFrameworkDiscoveryOptions discoveryOptions,
        ITestMethod testMethod,
        IAttributeInfo theoryAttribute)
    {
        yield return new PineconeTheoryTestCase(
            this.DiagnosticMessageSink,
            discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(),
            testMethod);
    }

    protected override IEnumerable<IXunitTestCase> CreateTestCasesForDataRow(
        ITestFrameworkDiscoveryOptions discoveryOptions,
        ITestMethod testMethod,
        IAttributeInfo theoryAttribute,
        object[] dataRow)
    {
        yield return new PineconeFactTestCase(
            this.DiagnosticMessageSink,
            discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(),
            testMethod,
            dataRow);
    }
}
