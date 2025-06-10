// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace VectorData.ConformanceTests.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("VectorDataSpecificationTests.Xunit.ConditionalFactDiscoverer", "VectorData.ConformanceTests")]
public sealed class ConditionalFactAttribute : FactAttribute;
