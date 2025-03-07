// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

namespace VectorDataSpecificationTests.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("VectorDataSpecificationTests.Xunit.ConditionalFactDiscoverer", "VectorDataIntegrationTests")]
public sealed class ConditionalFactAttribute : FactAttribute;
