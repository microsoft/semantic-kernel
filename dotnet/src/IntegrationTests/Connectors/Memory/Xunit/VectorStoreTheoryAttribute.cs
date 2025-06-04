// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("SemanticKernel.IntegrationTests.Connectors.Memory.Xunit.VectorStoreTheoryDiscoverer", "IntegrationTests")]
public sealed class VectorStoreTheoryAttribute : TheoryAttribute;
