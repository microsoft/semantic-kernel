// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Azure;
using Azure.AI.FormRecognizer;
using Azure.AI.FormRecognizer.Models;
using Microsoft.AspNetCore.Http;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Wrapper for the Azure.AI.FormRecognizer. This allows Form Recognizer to be used as the OCR engine for reading text from files with an image MIME type.
/// </summary>
public class AzureFormRecognizerOcrEngine : IOcrEngine
{
    /// <summary>
    /// Creates a new instance of the AzureFormRecognizerOcrEngine passing in the Form Recognizer endpoint and key.
    /// </summary>
    /// <param name="endpoint">The endpoint for accessing a provisioned Azure Form Recognizer instance</param>
    /// <param name="credential">The AzureKeyCredential containing the provisioned Azure Form Recognizer access key</param>
    public AzureFormRecognizerOcrEngine(string endpoint, AzureKeyCredential credential)
    {
        this.FormRecognizerClient = new FormRecognizerClient(new Uri(endpoint), credential);
    }

    public FormRecognizerClient FormRecognizerClient { get; }

    ///<inheritdoc/>
    public async Task<string> ReadTextFromImageFileAsync(IFormFile imageFile)
    {
        await using (var ms = new MemoryStream())
        {
            await imageFile.CopyToAsync(ms);
            var fileBytes = ms.ToArray();
            await using var imgStream = new MemoryStream(fileBytes);

            // Start the OCR operation
            RecognizeContentOperation operation = await this.FormRecognizerClient.StartRecognizeContentAsync(imgStream);

            // Wait for the result
            Response<FormPageCollection> operationResponse = await operation.WaitForCompletionAsync();
            FormPageCollection formPages = operationResponse.Value;

            // Get the text content
            StringBuilder text = new();
            foreach (FormPage page in formPages)
            {
                foreach (FormLine line in page.Lines)
                {
                    foreach (FormWord word in line.Words)
                    {
                        text.Append(word.Text);
                        text.Append(' ');
                    }
                    text.AppendLine();
                }
            }
            return text.ToString();
        }
    }
}
