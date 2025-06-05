// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace VectorData.ConformanceTests.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("VectorDataSpecificationTests.Xunit.ConditionalTheoryDiscoverer", "VectorData.ConformanceTests")]
public sealed class ConditionalTheoryAttribute : TheoryAttribute;
