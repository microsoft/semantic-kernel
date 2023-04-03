// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.TestExtensions;

[XunitTestCaseDiscoverer("SemanticKernel.IntegrationTests.TestExtensions.SkippableFactDiscoverer", "SemanticKernel.IntegrationTests")]
public class SkippableFactAttribute : FactAttribute
{
}
