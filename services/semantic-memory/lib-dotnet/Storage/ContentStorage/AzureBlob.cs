// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Identity;
using Azure.Storage;
using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;
using Azure.Storage.Blobs.Specialized;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Services.Diagnostics;

namespace Microsoft.SemanticKernel.Services.Storage.ContentStorage;

public class AzureBlob : IContentStorage
{
    private readonly BlobContainerClient _containerClient;
    private readonly string _containerName;
    private readonly ILogger<AzureBlob> _log;

    public AzureBlob(
        string connectionString,
        string containerName = "skmemory",
        ILogger<AzureBlob>? logger = null)
        : this(new BlobServiceClient(connectionString), containerName, logger)
    {
    }

    public AzureBlob(
        string accountName,
        string endpointSuffix = "core.windows.net",
        string containerName = "skmemory",
        ILogger<AzureBlob>? logger = null)
        : this(new BlobServiceClient(
            new Uri($"https://{accountName}.blob.{endpointSuffix}"),
            new DefaultAzureCredential()), containerName, logger)
    {
    }

    public AzureBlob(
        string accountName,
        string accountKey,
        string endpointSuffix = "core.windows.net",
        string containerName = "skmemory",
        ILogger<AzureBlob>? logger = null)
        : this(new BlobServiceClient(
            new Uri($"https://{accountName}.blob.{endpointSuffix}"),
            new StorageSharedKeyCredential(accountName, accountKey)), containerName, logger)
    {
    }

    public AzureBlob(BlobServiceClient client, string containerName = "skmemory", ILogger<AzureBlob>? logger = null)
    {
        if (string.IsNullOrEmpty(containerName))
        {
            throw new ContentStorageException("The container name is empty");
        }

        this._containerName = containerName;
        this._containerClient = client.GetBlobContainerClient(containerName);

        if (this._containerClient == null)
        {
            throw new ContentStorageException("Unable to instantiate Azure Blob container client");
        }

        this._log = logger ?? NullLogger<AzureBlob>.Instance;
    }

    /// <inherit />
    public async Task CreateDirectoryAsync(string directoryName, CancellationToken cancellationToken = default)
    {
        this._log.LogTrace("Creating container '{0}' ...", this._containerName);

        await this._containerClient
            .CreateIfNotExistsAsync(PublicAccessType.None, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        this._log.LogTrace("Container '{0}' ready", this._containerName);
    }

    /// <inherit />
    public Task WriteTextFileAsync(string directoryName, string fileName, string fileContent, CancellationToken cancellationToken = default)
    {
        return this.InternalWriteAsync(directoryName, fileName, fileContent, cancellationToken);
    }

    /// <inherit />
    public Task<long> WriteStreamAsync(string directoryName, string fileName, Stream contentStream, CancellationToken cancellationToken = default)
    {
        return this.InternalWriteAsync(directoryName, fileName, contentStream, cancellationToken);
    }

    /// <inherit />
    public async Task<BinaryData> ReadFileAsync(string directoryName, string fileName, CancellationToken cancellationToken = default)
    {
        var blobName = $"{directoryName}/{fileName}";
        BlobClient blobClient = this.GetBlobClient(blobName);
        Response<BlobDownloadResult>? content = await blobClient.DownloadContentAsync(cancellationToken).ConfigureAwait(false);

        if (content == null || !content.HasValue)
        {
            this._log.LogError("Unable to download file {0}", blobName);
            throw new ContentStorageException("Unable to fetch blob content");
        }

        return content.Value.Content;
    }

    private async Task<long> InternalWriteAsync(string directoryName, string fileName, object content, CancellationToken cancellationToken)
    {
        var blobName = $"{directoryName}/{fileName}";

        BlobClient blobClient = this.GetBlobClient(blobName);

        BlobUploadOptions options = new();
        BlobLeaseClient? blobLeaseClient = null;
        BlobLease? lease = null;
        if (await blobClient.ExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            blobLeaseClient = this.GetBlobLeaseClient(blobClient);
            lease = await this.LeaseBlobAsync(blobLeaseClient, cancellationToken).ConfigureAwait(false);
            options = new BlobUploadOptions { Conditions = new BlobRequestConditions { LeaseId = lease.LeaseId } };
        }

        this._log.LogTrace("Writing blob {0} ...", blobName);

        long size;
        if (content is string fileContent)
        {
            await blobClient.UploadAsync(BinaryData.FromString(fileContent), options, cancellationToken).ConfigureAwait(false);
            size = fileContent.Length;
        }
        else
        {
            var stream = content as Stream;
            await blobClient.UploadAsync(stream, options, cancellationToken).ConfigureAwait(false);
            size = stream!.Length;
        }

        await this.ReleaseBlobAsync(blobLeaseClient, lease, cancellationToken).ConfigureAwait(false);

        this._log.LogTrace("Blob {0} ready, size {1}", blobName, size);

        return size;
    }

    private BlobClient GetBlobClient(string blobName)
    {
        BlobClient? blobClient = this._containerClient.GetBlobClient(blobName);
        if (blobClient == null)
        {
            throw new ContentStorageException("Unable to instantiate Azure Blob blob client");
        }

        return blobClient;
    }

    private BlobLeaseClient GetBlobLeaseClient(BlobClient blobClient)
    {
        var blobLeaseClient = blobClient.GetBlobLeaseClient();
        if (blobLeaseClient == null)
        {
            throw new ContentStorageException("Unable to instantiate Azure blob lease client");
        }

        return blobLeaseClient;
    }

    private async Task<BlobLease> LeaseBlobAsync(BlobLeaseClient blobLeaseClient, CancellationToken cancellationToken)
    {
        this._log.LogTrace("Leasing blob {0} ...", blobLeaseClient.Uri);

        Response<BlobLease> lease = await blobLeaseClient
            .AcquireAsync(TimeSpan.FromSeconds(30), cancellationToken: cancellationToken)
            .ConfigureAwait(false);
        if (lease == null || !lease.HasValue)
        {
            throw new ContentStorageException("Unable to lease blob");
        }

        this._log.LogTrace("Blob {0} leased", blobLeaseClient.Uri);

        return lease.Value;
    }

    private async Task ReleaseBlobAsync(BlobLeaseClient? blobLeaseClient, BlobLease? lease, CancellationToken cancellationToken)
    {
        if (lease != null && blobLeaseClient != null)
        {
            this._log.LogTrace("Releasing blob {0} ...", blobLeaseClient.Uri);
            await blobLeaseClient
                .ReleaseAsync(new BlobRequestConditions { LeaseId = lease.LeaseId }, cancellationToken: cancellationToken)
                .ConfigureAwait(false);
            this._log.LogTrace("Blob released {0} ...", blobLeaseClient.Uri);
        }
    }
}
