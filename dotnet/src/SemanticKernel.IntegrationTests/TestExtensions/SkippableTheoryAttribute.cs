// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.TestExtensions;

[XunitTestCaseDiscoverer("SemanticKernel.IntegrationTests.TestExtensions.SkippableTheoryDiscoverer", "SemanticKernel.IntegrationTests")]
public sealed class SkippableTheoryAttribute : TheoryAttribute
{
}
