// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Files;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTestsV2.Connectors.OpenAI;

public sealed class OpenAIFileServiceTests()
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIFileServiceTests>()
        .Build();

    [Theory]
    [InlineData("test_image_001.jpg", "image/jpeg")]
    [InlineData("test_content.txt", "text/plain")]
    public async Task OpenAIFileServiceLifecycleAsync(string fileName, string mimeType)
    {
        // Arrange
        var fileService = this.CreateOpenAIFileService();

        // Setup file content
        await using FileStream fileStream = File.OpenRead($"./TestData/{fileName}");
        BinaryData sourceData = await BinaryData.FromStreamAsync(fileStream);
        BinaryContent sourceContent = new(sourceData.ToArray(), mimeType);

        // Upload file
        OpenAIFileInfo fileInfo = await fileService.UploadContentAsync(sourceContent, new(fileName, FileUploadPurpose.FineTune));
        try
        {
            AssertFileReferenceEquals(fileInfo, fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve files by different purpose
            Dictionary<string, OpenAIFileInfo> fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.Vision);
            Assert.DoesNotContain(fileInfo.Id, fileMap.Keys);

            // Retrieve files by expected purpose
            fileMap = await GetFilesAsync(fileService, OpenAIFilePurpose.FineTune);
            Assert.Contains(fileInfo.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileInfo.Id], fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve files by no specific purpose
            fileMap = await GetFilesAsync(fileService);
            Assert.Contains(fileInfo.Id, fileMap.Keys);
            AssertFileReferenceEquals(fileMap[fileInfo.Id], fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve file by id
            OpenAIFileInfo file = await fileService.GetFileAsync(fileInfo.Id);
            AssertFileReferenceEquals(file, fileName, sourceData.Length, OpenAIFilePurpose.FineTune);

            // Retrieve file content
            BinaryContent retrievedContent = await fileService.GetFileContentAsync(fileInfo.Id);
            Assert.NotNull(retrievedContent.Data);
            Assert.NotNull(retrievedContent.Metadata);
            Assert.Equal(fileInfo.Id, retrievedContent.Metadata!["fileId"]);
            Assert.Equal(sourceContent.Data!.Value.Length, retrievedContent.Data.Value.Length);
        }
        finally
        {
            // Delete file
            await fileService.DeleteFileAsync(fileInfo.Id);
        }
    }

    private static void AssertFileReferenceEquals(OpenAIFileInfo fileInfo, string expectedFileName, int expectedSize, OpenAIFilePurpose expectedPurpose)
    {
        Assert.Equal(expectedFileName, fileInfo.Filename);
        Assert.Equal(expectedPurpose, fileInfo.Purpose);
        Assert.Equal(expectedSize, fileInfo.SizeInBytes);
    }

    private static async Task<Dictionary<string, OpenAIFileInfo>> GetFilesAsync(OpenAIFileService fileService, OpenAIFilePurpose? purpose = null)
    {
        IEnumerable<OpenAIFileInfo> files = await fileService.GetFilesAsync(purpose);
        Dictionary<string, OpenAIFileInfo> fileIds = files.DistinctBy(f => f.Id).ToDictionary(f => f.Id);
        return fileIds;
    }

    private OpenAIFileService CreateOpenAIFileService()
    {
        var OpenAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(OpenAIConfiguration);
        Assert.NotNull(OpenAIConfiguration.ApiKey);
        Assert.NotNull(OpenAIConfiguration.ServiceId);

        return new(OpenAIConfiguration.ApiKey);
    }
}
