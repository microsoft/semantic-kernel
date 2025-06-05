// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Containers;

namespace Weaviate.ConformanceTests.Support.TestContainer;

public class WeaviateContainer(WeaviateConfiguration configuration) : DockerContainer(configuration);
