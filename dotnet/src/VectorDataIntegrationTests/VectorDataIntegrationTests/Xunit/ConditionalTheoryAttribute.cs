// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace VectorDataSpecificationTests.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("VectorDataSpecificationTests.Xunit.VectorStoreFactDiscoverer", "VectorDataIntegrationTests")]
public sealed class ConditionalTheoryAttribute : TheoryAttribute;
