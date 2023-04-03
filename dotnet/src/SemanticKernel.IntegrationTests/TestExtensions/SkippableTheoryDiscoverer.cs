// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.TestExtensions;

public class SkippableTheoryDiscoverer : IXunitTestCaseDiscoverer
{
    private readonly IMessageSink _diagnosticMessageSink;
    private readonly TheoryDiscoverer _theoryDiscoverer;

    public SkippableTheoryDiscoverer(IMessageSink diagnosticMessageSink)
    {
        this._diagnosticMessageSink = diagnosticMessageSink;

        this._theoryDiscoverer = new TheoryDiscoverer(diagnosticMessageSink);
    }

    public IEnumerable<IXunitTestCase> Discover(ITestFrameworkDiscoveryOptions discoveryOptions, ITestMethod testMethod, IAttributeInfo factAttribute)
    {
        var defaultMethodDisplay = discoveryOptions.MethodDisplayOrDefault();
        var defaultMethodDisplayOptions = discoveryOptions.MethodDisplayOptionsOrDefault();

        // Unlike fact discovery, the underlying algorithm for theories is complex, so we let the theory discoverer
        // do its work, and do a little on-the-fly conversion into our own test cases.
        return this._theoryDiscoverer.Discover(discoveryOptions, testMethod, factAttribute)
            .Select(testCase => testCase is XunitTheoryTestCase
                ? (IXunitTestCase)new SkippableTheoryTestCase(this._diagnosticMessageSink, defaultMethodDisplay, defaultMethodDisplayOptions, testCase.TestMethod)
                : new SkippableFactTestCase(this._diagnosticMessageSink, defaultMethodDisplay, defaultMethodDisplayOptions, testCase.TestMethod,
                    testCase.TestMethodArguments));
    }
}
