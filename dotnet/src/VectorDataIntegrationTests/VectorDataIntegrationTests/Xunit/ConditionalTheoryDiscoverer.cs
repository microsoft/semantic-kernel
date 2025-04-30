// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;
using Xunit.Sdk;

namespace VectorDataSpecificationTests.Xunit;

/// <summary>
///     Used dynamically from <see cref="ConditionalTheoryAttribute" />.
///     Make sure to update that class if you move this type.
/// </summary>
public class ConditionalTheoryDiscoverer(IMessageSink messageSink) : TheoryDiscoverer(messageSink)
{
    protected override IEnumerable<IXunitTestCase> CreateTestCasesForTheory(
        ITestFrameworkDiscoveryOptions discoveryOptions,
        ITestMethod testMethod,
        IAttributeInfo theoryAttribute)
    {
        yield return new ConditionalTheoryTestCase(
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
        yield return new ConditionalFactTestCase(
            this.DiagnosticMessageSink,
            discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(),
            testMethod,
            dataRow);
    }
}
