// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit.PineconeTheoryDiscoverer", "IntegrationTests")]
public sealed class PineconeTheoryAttribute : TheoryAttribute;
