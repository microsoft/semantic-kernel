// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Primitives;

namespace Microsoft.SemanticKernel.Services.SemanticMemory.WebService;

public class UploadRequest
{
    public string RequestId { get; set; } = string.Empty;
    public string UserId { get; set; } = string.Empty;
    public IEnumerable<string> VaultIds { get; set; } = new List<string>();
    public IEnumerable<IFormFile> Files { get; set; } = new List<IFormFile>();

    /* Resources:
     * https://learn.microsoft.com/en-us/aspnet/core/mvc/models/file-uploads?view=aspnetcore-7.0
     * https://learn.microsoft.com/en-us/aspnet/core/mvc/models/file-uploads?view=aspnetcore-7.0#upload-large-files-with-streaming
     * https://stackoverflow.com/questions/71499435/how-do-i-do-file-upload-using-asp-net-core-6-minimal-api
     * https://stackoverflow.com/questions/57033535/multipartformdatacontent-add-stringcontent-is-adding-carraige-return-linefeed-to
     */
    public static async Task<(UploadRequest model, bool isValid, string errMsg)> BindHttpRequestAsync(HttpRequest httpRequest)
    {
        const string UserField = "user";
        const string VaultsField = "vaults";
        const string RequestIdField = "requestId";

        var result = new UploadRequest();

        // Content format validation
        if (!httpRequest.HasFormContentType)
        {
            return (result, false, "Invalid content, multipart form data not found");
        }

        // Read form
        IFormCollection form = await httpRequest.ReadFormAsync();

        // There must be at least one file
        if (form.Files.Count == 0)
        {
            return (result, false, "No file was uploaded");
        }

        // TODO: extract user ID from auth headers
        if (!form.TryGetValue(UserField, out StringValues userIds) || userIds.Count != 1 || string.IsNullOrEmpty(userIds[0]))
        {
            return (result, false, $"Invalid or missing user ID, '{UserField}' value empty or not found, or multiple values provided");
        }

        // At least one vault must be specified.Note: the pipeline might decide to ignore the specified vaults, 
        // i.e. custom pipelines can override/ignore this value, depending on the implementation chosen. 
        if (!form.TryGetValue(VaultsField, out StringValues vaultIds) || vaultIds.Count == 0 || vaultIds.Any(string.IsNullOrEmpty))
        {
            return (result, false, $"Invalid or missing vault ID, '{VaultsField}' list is empty or contains empty values");
        }

        if (form.TryGetValue(RequestIdField, out StringValues requestIds) && requestIds.Count > 1)
        {
            return (result, false, $"Invalid request ID, '{RequestIdField}' must be a single value, not a list");
        }

        // Request Id is optional, e.g. the client wants to retry the same upload, otherwise we generate a random/unique one
        result.RequestId = requestIds.FirstOrDefault() ?? DateTimeOffset.Now.ToString("yyyyMMdd.HHmmss.") + Guid.NewGuid().ToString("N");

        result.UserId = userIds[0]!;
        result.VaultIds = vaultIds;
        result.Files = form.Files;

        return (result, true, string.Empty);
    }
}
