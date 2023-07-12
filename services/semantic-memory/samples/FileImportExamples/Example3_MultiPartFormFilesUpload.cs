// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

public static class Example3_MultiPartFormFilesUpload
{
    public static async Task RunAsync()
    {
        Console.WriteLine("=== File upload using multipart form example ===");
        Console.WriteLine("* Preparing web request...");

        // Request ID
        string requestId = Guid.NewGuid().ToString("D");

        // User ID
        string userId = "user12099";

        // List of vaults
        string vaultId1 = "vaultABC";
        string vaultId2 = "xyz";

        // Connect to localhost web service
        var client = new HttpClient();
        client.BaseAddress = new Uri("http://127.0.0.1:9001/");
        Console.WriteLine($"* Preparing client to {client.BaseAddress}...");

        // Populate form with values and files from disk
        using var formData = new MultipartFormDataContent();

        Console.WriteLine("* Adding values to form...");
        formData.Add(new StringContent(requestId), "requestId");
        formData.Add(new StringContent(userId), "user");
        formData.Add(new StringContent(vaultId1), "vaults");
        formData.Add(new StringContent(vaultId2), "vaults");

        Console.WriteLine("* Adding files to form...");
        await UploadFileAsync(formData, "file1", "file1.txt");
        await UploadFileAsync(formData, "file2", "file2.txt");
        await UploadFileAsync(formData, "file3", "file3.docx");
        await UploadFileAsync(formData, "file4", "file4.pdf");

        // Send HTTP request
        Console.WriteLine("* Sending HTTP request");
        var response = await client.PostAsync("/upload", formData);

        Console.WriteLine("== RESPONSE ==");
        Console.WriteLine(response.StatusCode.ToString("G"));
        Console.WriteLine((int)response.StatusCode);
        Console.WriteLine(await response.Content.ReadAsStringAsync());
        Console.WriteLine("== END ==");

        Console.WriteLine("File upload completed.");
    }

    // Read file from disk and add it to the form
    private static async Task UploadFileAsync(MultipartFormDataContent form, string name, string filename)
    {
        byte[] bytes = await File.ReadAllBytesAsync(filename);
        var content = new StreamContent(new BinaryData(bytes).ToStream());
        form.Add(content, name, filename);
    }
}
