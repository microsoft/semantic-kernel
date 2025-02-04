// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Containers;

namespace WeaviateIntegrationTests.Support.TestContainer;

public class WeaviateContainer(WeaviateConfiguration configuration) : DockerContainer(configuration);
