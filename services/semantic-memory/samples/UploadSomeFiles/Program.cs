// Copyright (c) Microsoft. All rights reserved.

namespace FilesUploadApp;

#pragma warning disable CA2000
public class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main(string[] args)
    {
        Console.WriteLine("Starting...");

        // Request ID
        string requestId = Guid.NewGuid().ToString("D");

        // User ID
        string userId = "user98033";

        // List of vaults
        string vaultId1 = "vaultABC";
        string vaultId2 = "xyz";

        // Connect to localhost web service
        var client = new HttpClient();
        client.BaseAddress = new Uri("http://127.0.0.1:9001/");

        // Populate form with values and files from disk
        using var formData = new MultipartFormDataContent();

        formData.Add(new StringContent(requestId), "requestId");
        formData.Add(new StringContent(userId), "user");
        formData.Add(new StringContent(vaultId1), "vaults");
        formData.Add(new StringContent(vaultId2), "vaults");

        await UploadFileAsync(formData, "file1", "file1.txt");
        await UploadFileAsync(formData, "file2", "file2.txt");
        await UploadFileAsync(formData, "file3", "file3.docx");
        await UploadFileAsync(formData, "file4", "file4.pdf");

        // Send HTTP request
        Console.WriteLine("Sending request");
        var response = await client.PostAsync("/upload", formData);

        Console.WriteLine("== RESPONSE ==");
        Console.WriteLine(response.StatusCode.ToString("G"));
        Console.WriteLine((int)response.StatusCode);
        Console.WriteLine(await response.Content.ReadAsStringAsync());
        Console.WriteLine("== END ==");
    }

    // Read file from disk and add it to the form
    private static async Task UploadFileAsync(MultipartFormDataContent form, string name, string filename)
    {
        byte[] bytes = await File.ReadAllBytesAsync(filename);
        var content = new StreamContent(new BinaryData(bytes).ToStream());
        form.Add(content, name, filename);
    }
}
