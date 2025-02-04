// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Containers;
using Microsoft.Extensions.Logging;

namespace QdrantIntegrationTests.Support.TestContainer;

public class QdrantContainer(QdrantConfiguration configuration) : DockerContainer(configuration);
