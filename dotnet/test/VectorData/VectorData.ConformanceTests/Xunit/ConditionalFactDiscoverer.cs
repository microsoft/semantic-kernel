// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;
using Xunit.Sdk;

namespace VectorData.ConformanceTests.Xunit;

/// <summary>
///     Used dynamically from <see cref="ConditionalFactAttribute" />.
///     Make sure to update that class if you move this type.
/// </summary>
public class ConditionalFactDiscoverer(IMessageSink messageSink) : FactDiscoverer(messageSink)
{
    protected override IXunitTestCase CreateTestCase(
        ITestFrameworkDiscoveryOptions discoveryOptions,
        ITestMethod testMethod,
        IAttributeInfo factAttribute)
        => new ConditionalFactTestCase(
            this.DiagnosticMessageSink,
            discoveryOptions.MethodDisplayOrDefault(),
            discoveryOptions.MethodDisplayOptionsOrDefault(),
            testMethod);
}
