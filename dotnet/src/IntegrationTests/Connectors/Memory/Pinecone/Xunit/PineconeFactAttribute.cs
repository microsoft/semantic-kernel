// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

[AttributeUsage(AttributeTargets.Method)]
[XunitTestCaseDiscoverer("SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit.PineconeFactDiscoverer", "IntegrationTests")]
public sealed class PineconeFactAttribute : FactAttribute;
