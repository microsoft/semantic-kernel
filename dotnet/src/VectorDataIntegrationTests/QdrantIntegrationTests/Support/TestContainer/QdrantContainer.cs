// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Containers;

namespace QdrantIntegrationTests.Support.TestContainer;

public class QdrantContainer(QdrantConfiguration configuration) : DockerContainer(configuration);
