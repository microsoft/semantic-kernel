// Copyright (c) Microsoft. All rights reserved.

using Docker.DotNet.Models;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;
using Qdrant.Client.Grpc;

namespace QdrantIntegrationTests.Support.TestContainer;

public sealed class QdrantBuilder : ContainerBuilder<QdrantBuilder, QdrantContainer, QdrantConfiguration>
{
    public const string QdrantImage = "qdrant/qdrant:" + QdrantGrpcClient.QdrantVersion;

    public const ushort QdrantHttpPort = 6333;

    public const ushort QdrantGrpcPort = 6334;

    public QdrantBuilder() : this(new QdrantConfiguration()) => this.DockerResourceConfiguration = this.Init().DockerResourceConfiguration;

    private QdrantBuilder(QdrantConfiguration dockerResourceConfiguration) : base(dockerResourceConfiguration)
        => this.DockerResourceConfiguration = dockerResourceConfiguration;

    public QdrantBuilder WithConfigFile(string configPath)
        => this.Merge(this.DockerResourceConfiguration, new QdrantConfiguration())
            .WithBindMount(configPath, "/qdrant/config/custom_config.yaml");

    public QdrantBuilder WithCertificate(string certPath, string keyPath)
        => this.Merge(this.DockerResourceConfiguration, new QdrantConfiguration())
            .WithBindMount(certPath, "/qdrant/tls/cert.pem")
            .WithBindMount(keyPath, "/qdrant/tls/key.pem");

    public override QdrantContainer Build()
    {
        this.Validate();
        return new QdrantContainer(this.DockerResourceConfiguration);
    }

    protected override QdrantBuilder Init()
        => base.Init()
            .WithImage(QdrantImage)
            .WithPortBinding(QdrantHttpPort, true)
            .WithPortBinding(QdrantGrpcPort, true)
            .WithWaitStrategy(Wait.ForUnixContainer()
                .UntilMessageIsLogged(".*Actix runtime found; starting in Actix runtime.*"));

    protected override QdrantBuilder Clone(IResourceConfiguration<CreateContainerParameters> resourceConfiguration)
        => this.Merge(this.DockerResourceConfiguration, new QdrantConfiguration(resourceConfiguration));

    protected override QdrantBuilder Merge(QdrantConfiguration oldValue, QdrantConfiguration newValue)
        => new(new QdrantConfiguration(oldValue, newValue));

    protected override QdrantConfiguration DockerResourceConfiguration { get; }

    protected override QdrantBuilder Clone(IContainerConfiguration resourceConfiguration)
        => this.Merge(this.DockerResourceConfiguration, new QdrantConfiguration(resourceConfiguration));
}
