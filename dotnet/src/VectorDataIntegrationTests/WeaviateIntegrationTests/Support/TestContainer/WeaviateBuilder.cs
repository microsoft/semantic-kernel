// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet.Models;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;

namespace WeaviateIntegrationTests.Support.TestContainer;

public sealed class WeaviateBuilder : ContainerBuilder<WeaviateBuilder, WeaviateContainer, WeaviateConfiguration>
{
    public const string WeaviateImage = "semitechnologies/weaviate:1.28.12";
    public const ushort WeaviateHttpPort = 8080;
    public const ushort WeaviateGrpcPort = 50051;

    public WeaviateBuilder() : this(new WeaviateConfiguration()) => this.DockerResourceConfiguration = this.Init().DockerResourceConfiguration;

    private WeaviateBuilder(WeaviateConfiguration dockerResourceConfiguration) : base(dockerResourceConfiguration)
        => this.DockerResourceConfiguration = dockerResourceConfiguration;

    public override WeaviateContainer Build()
    {
        this.Validate();
        return new WeaviateContainer(this.DockerResourceConfiguration);
    }

    protected override WeaviateBuilder Init()
        => base.Init()
            .WithImage(WeaviateImage)
            .WithPortBinding(WeaviateHttpPort, true)
            .WithPortBinding(WeaviateGrpcPort, true)
            .WithEnvironment("AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED", "true")
            .WithEnvironment("PERSISTENCE_DATA_PATH", "/var/lib/weaviate")
            .WithWaitStrategy(Wait.ForUnixContainer()
                .UntilPortIsAvailable(WeaviateHttpPort)
                .UntilPortIsAvailable(WeaviateGrpcPort)
                .UntilHttpRequestIsSucceeded(r => r.ForPath("/v1/.well-known/ready").ForPort(WeaviateHttpPort)));

    protected override WeaviateBuilder Clone(IResourceConfiguration<CreateContainerParameters> resourceConfiguration)
        => this.Merge(this.DockerResourceConfiguration, new WeaviateConfiguration(resourceConfiguration));

    protected override WeaviateBuilder Merge(WeaviateConfiguration oldValue, WeaviateConfiguration newValue)
        => new(new WeaviateConfiguration(oldValue, newValue));

    protected override WeaviateConfiguration DockerResourceConfiguration { get; }

    protected override WeaviateBuilder Clone(IContainerConfiguration resourceConfiguration)
        => this.Merge(this.DockerResourceConfiguration, new WeaviateConfiguration(resourceConfiguration));
}
