// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using OpenAI.Files;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTestsV2.Connectors.AzureOpenAI;

public sealed class AzureOpenAIFileServiceTests()
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIFileServiceTests>()
        .Build();

    [Theory(Skip = "Temporarily skipped until the issue 'HTTP 400 (invalidPayload) Invalid value for purpose.' is fixed. See: https://github.com/microsoft/semantic-kernel/issues/7167")]
    [InlineData("test_image_001.jpg", "image/jpeg")]
    [InlineData("test_content.txt", "text/plain")]
    public async Task AzureOpenAIFileServiceLifecycleAsync(string fileName, string mimeType)
    {
        // Arrange
        var fileService = this.CreateAzureOpenAIFileService();

        // Setup file content
        await using FileStream fileStream = File.OpenRead($"./TestData/{fileName}");
        BinaryData sourceData = await BinaryData.FromStreamAsync(fileStream);
        BinaryContent sourceContent = new(sourceData.ToArray(), mimeType);

        // Upload file
        AzureOpenAIFileReference fileReference = await fileService.UploadContentAsync(sourceContent, new(fileName, FileUploadPurpose.Assistants));
        try
        {
            AssertFileReferenceEquals(fileReference, fileName, sourceData.Length, OpenAIFilePurpose.Assistants);

            // Retrieve files by different purpose
            Dictionary<string, AzureOpenAIFileReference> fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.FineTune);
            Assert.DoesNotContain(fileReference.Id, fileMap.Keys);

            // Retrieve files by expected purpose
            fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.Assistants);
            Assert.Contains(fileReference.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileReference.Id], fileName, sourceData.Length, OpenAIFilePurpose.Assistants);

            // Retrieve files by no specific purpose
            fileMap = await GetFilesAsync(fileService);
            Assert.Contains(fileReference.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileReference.Id], fileName, sourceData.Length, OpenAIFilePurpose.Assistants);

            // Retrieve file by id
            AzureOpenAIFileReference file = await fileService.GetFileAsync(fileReference.Id);
            AssertFileReferenceEquals(file, fileName, sourceData.Length, OpenAIFilePurpose.Assistants);

            // Retrieve file content
            BinaryContent retrievedContent = await fileService.GetFileContentAsync(fileReference.Id);
            Assert.NotNull(retrievedContent.Data);
            Assert.NotNull(retrievedContent.Uri);
            Assert.NotNull(retrievedContent.Metadata);
            Assert.Equal(fileReference.Id, retrievedContent.Metadata["id"]);
            Assert.Equal(sourceContent.Data!.Value.Length, retrievedContent.Data.Value.Length);
        }
        finally
        {
            // Delete file
            await fileService.DeleteFileAsync(fileReference.Id);
        }
    }

    private static void AssertFileReferenceEquals(AzureOpenAIFileReference fileReference, string expectedFileName, int expectedSize, OpenAIFilePurpose expectedPurpose)
    {
        Assert.Equal(expectedFileName, fileReference.FileName);
        Assert.Equal(expectedPurpose, fileReference.Purpose);
        Assert.Equal(expectedSize, fileReference.SizeInBytes);
    }

    private static async Task<Dictionary<string, AzureOpenAIFileReference>> GetFilesAsync(AzureOpenAIFileService fileService, OpenAIFilePurpose? purpose = null)
    {
        IEnumerable<AzureOpenAIFileReference> files = await fileService.GetFilesAsync(purpose);
        Dictionary<string, AzureOpenAIFileReference> fileIds = files.DistinctBy(f => f.Id).ToDictionary(f => f.Id);
        return fileIds;
    }

    private AzureOpenAIFileService CreateAzureOpenAIFileService()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        return new(new Uri(azureOpenAIConfiguration.Endpoint), azureOpenAIConfiguration.ApiKey);
    }
}
