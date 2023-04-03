// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.TestExtensions;

public class SkippableFactDiscoverer : IXunitTestCaseDiscoverer
{
    private readonly IMessageSink _diagnosticMessageSink;

    public SkippableFactDiscoverer(IMessageSink diagnosticMessageSink)
    {
        this._diagnosticMessageSink = diagnosticMessageSink;
    }

    public IEnumerable<IXunitTestCase> Discover(ITestFrameworkDiscoveryOptions discoveryOptions, ITestMethod testMethod, IAttributeInfo factAttribute)
    {
        yield return new SkippableFactTestCase(this._diagnosticMessageSink, discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(), testMethod);
    }
}
