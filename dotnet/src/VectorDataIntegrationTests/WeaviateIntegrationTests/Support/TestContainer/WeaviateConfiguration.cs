// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet.Models;
using DotNet.Testcontainers.Configurations;

namespace WeaviateIntegrationTests.Support.TestContainer;

public sealed class WeaviateConfiguration : ContainerConfiguration
{
    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateConfiguration" /> class.
    /// </summary>
    public WeaviateConfiguration()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public WeaviateConfiguration(IResourceConfiguration<CreateContainerParameters> resourceConfiguration)
        : base(resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public WeaviateConfiguration(IContainerConfiguration resourceConfiguration)
        : base(resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateConfiguration" /> class.
    /// </summary>
    /// <param name="resourceConfiguration">The Docker resource configuration.</param>
    public WeaviateConfiguration(WeaviateConfiguration resourceConfiguration)
        : this(new WeaviateConfiguration(), resourceConfiguration)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateConfiguration" /> class.
    /// </summary>
    /// <param name="oldValue">The old Docker resource configuration.</param>
    /// <param name="newValue">The new Docker resource configuration.</param>
    public WeaviateConfiguration(WeaviateConfiguration oldValue, WeaviateConfiguration newValue)
        : base(oldValue, newValue)
    {
    }
}
