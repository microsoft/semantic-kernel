// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

[Obsolete("This class is deprecated and will be removed in a future version.")]
public sealed class OpenAIFileServiceTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIFileServiceTests>()
        .Build();

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("test_image_001.jpg", "image/jpeg")]
    [InlineData("test_content.txt", "text/plain")]
    public async Task OpenAIFileServiceLifecycleAsync(string fileName, string mimeType)
    {
        // Arrange
        OpenAIFileService fileService = this.CreateOpenAIFileService();

        // Act & Assert
        await this.VerifyFileServiceLifecycleAsync(fileService, fileName, mimeType);
    }

    [Theory]
    [InlineData("test_image_001.jpg", "image/jpeg")]
    [InlineData("test_content.txt", "text/plain")]
    public async Task AzureOpenAIFileServiceLifecycleAsync(string fileName, string mimeType)
    {
        // Arrange
        OpenAIFileService fileService = this.CreateOpenAIFileService();

        // Act & Assert
        await this.VerifyFileServiceLifecycleAsync(fileService, fileName, mimeType);
    }

    private async Task VerifyFileServiceLifecycleAsync(OpenAIFileService fileService, string fileName, string mimeType)
    {
        // Setup file content
        await using FileStream fileStream = File.OpenRead($"./TestData/{fileName}");
        BinaryData sourceData = await BinaryData.FromStreamAsync(fileStream);
        BinaryContent sourceContent = new(sourceData.ToArray(), mimeType);

        // Upload file with unsupported purpose (failure case)
        await Assert.ThrowsAsync<HttpOperationException>(() => fileService.UploadContentAsync(sourceContent, new(fileName, OpenAIFilePurpose.AssistantsOutput)));

        // Upload file with wacky purpose (failure case)
        await Assert.ThrowsAsync<HttpOperationException>(() => fileService.UploadContentAsync(sourceContent, new(fileName, new OpenAIFilePurpose("pretend"))));

        // Upload file
        OpenAIFileReference fileReference = await fileService.UploadContentAsync(sourceContent, new(fileName, OpenAIFilePurpose.FineTune));
        try
        {
            AssertFileReferenceEquals(fileReference, fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve files by different purpose
            Dictionary<string, OpenAIFileReference> fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.Assistants);
            Assert.DoesNotContain(fileReference.Id, fileMap.Keys);

            // Retrieve files by wacky purpose (failure case)
            await Assert.ThrowsAsync<HttpOperationException>(() => GetFilesAsync(fileService, new OpenAIFilePurpose("pretend")));

            // Retrieve files by expected purpose
            fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.FineTune);
            Assert.Contains(fileReference.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileReference.Id], fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve files by no specific purpose
            fileMap = await GetFilesAsync(fileService);
            Assert.Contains(fileReference.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileReference.Id], fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve file by id
            OpenAIFileReference file = await fileService.GetFileAsync(fileReference.Id);
            AssertFileReferenceEquals(file, fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

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

    private static void AssertFileReferenceEquals(OpenAIFileReference fileReference, string expectedFileName, int expectedSize, OpenAIFilePurpose expectedPurpose)
    {
        Assert.Equal(expectedFileName, fileReference.FileName);
        Assert.Equal(expectedPurpose, fileReference.Purpose);
        Assert.Equal(expectedSize, fileReference.SizeInBytes);
    }

    private static async Task<Dictionary<string, OpenAIFileReference>> GetFilesAsync(OpenAIFileService fileService, OpenAIFilePurpose? purpose = null)
    {
        IEnumerable<OpenAIFileReference> files = await fileService.GetFilesAsync(purpose);
        Dictionary<string, OpenAIFileReference> fileIds = files.DistinctBy(f => f.Id).ToDictionary(f => f.Id);
        return fileIds;
    }

    #region internals

    private OpenAIFileService CreateOpenAIFileService()
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ApiKey);
        Assert.NotNull(openAIConfiguration.ServiceId);

        return new(openAIConfiguration.ApiKey, openAIConfiguration.ServiceId);
    }

    private OpenAIFileService CreateAzureOpenAIFileService()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        return new(new Uri(azureOpenAIConfiguration.Endpoint), azureOpenAIConfiguration.ApiKey, azureOpenAIConfiguration.ServiceId);
    }

    #endregion
}
