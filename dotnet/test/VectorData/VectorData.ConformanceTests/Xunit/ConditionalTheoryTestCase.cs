// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;
using Xunit.Sdk;

namespace VectorDataSpecificationTests.Xunit;

public sealed class ConditionalTheoryTestCase : XunitTheoryTestCase
{
    [Obsolete("Called by the de-serializer; should only be called by deriving classes for de-serialization purposes")]
    public ConditionalTheoryTestCase()
    {
    }

    public ConditionalTheoryTestCase(
        IMessageSink diagnosticMessageSink,
        TestMethodDisplay defaultMethodDisplay,
        TestMethodDisplayOptions defaultMethodDisplayOptions,
        ITestMethod testMethod)
        : base(diagnosticMessageSink, defaultMethodDisplay, defaultMethodDisplayOptions, testMethod)
    {
    }

    public override async Task<RunSummary> RunAsync(
        IMessageSink diagnosticMessageSink,
        IMessageBus messageBus,
        object[] constructorArguments,
        ExceptionAggregator aggregator,
        CancellationTokenSource cancellationTokenSource)
        => await XunitTestCaseExtensions.TrySkipAsync(this, messageBus)
            ? new RunSummary { Total = 1, Skipped = 1 }
            : await base.RunAsync(
                diagnosticMessageSink,
                messageBus,
                constructorArguments,
                aggregator,
                cancellationTokenSource);
}
