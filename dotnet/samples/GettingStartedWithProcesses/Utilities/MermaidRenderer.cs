// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using PuppeteerSharp;

namespace Utilities;

/// <summary>
/// Renders Mermaid diagrams to images using Puppeteer-Sharp.
/// </summary>
public static class MermaidRenderer
{
    /// <summary>
    /// Generates a Mermaid diagram image from the provided Mermaid code.
    /// </summary>
    /// <param name="mermaidCode"></param>
    /// <param name="filenameOrPath"></param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static async Task<string> GenerateMermaidImageAsync(string mermaidCode, string filenameOrPath)
    {
        // Ensure the filename has the correct .png extension
        if (!filenameOrPath.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("The filename must have a .png extension.", nameof(filenameOrPath));
        }

        string outputFilePath;

        // Check if the user provided an absolute path
        if (Path.IsPathRooted(filenameOrPath))
        {
            // Use the provided absolute path
            outputFilePath = filenameOrPath;

            // Ensure the directory exists
            string directoryPath = Path.GetDirectoryName(outputFilePath)
                ?? throw new InvalidOperationException("Could not determine the directory path.");
            if (!Directory.Exists(directoryPath))
            {
                throw new DirectoryNotFoundException($"The directory '{directoryPath}' does not exist.");
            }
        }
        else
        {
            // Use the assembly's directory for relative paths
            string? assemblyPath = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            if (assemblyPath == null)
            {
                throw new InvalidOperationException("Could not determine the assembly path.");
            }

            string outputPath = Path.Combine(assemblyPath, "output");
            Directory.CreateDirectory(outputPath); // Ensure output directory exists
            outputFilePath = Path.Combine(outputPath, filenameOrPath);
        }

        // Download Chromium if it hasn't been installed yet
        BrowserFetcher browserFetcher = new();
        browserFetcher.Browser = SupportedBrowser.Chrome;
        await browserFetcher.DownloadAsync();

        // Define the HTML template with Mermaid.js CDN
        string htmlContent = $@"
        <html>
            <head>
                <style>
                    body {{
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0;
                        height: 100vh;
                    }}
                </style>
                <script type=""module"">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
            </head>
            <body>
                <div class=""mermaid"">
                    {mermaidCode}
                </div>
            </body>
        </html>";

        // Create a temporary HTML file with the Mermaid code
        string tempHtmlFile = Path.Combine(Path.GetTempPath(), "mermaid_temp.html");
        try
        {
            await File.WriteAllTextAsync(tempHtmlFile, htmlContent);

            // Launch Puppeteer-Sharp with a headless browser to render the Mermaid diagram
            using (var browser = await Puppeteer.LaunchAsync(new LaunchOptions { Headless = true }))
            using (var page = await browser.NewPageAsync())
            {
                await page.GoToAsync($"file://{tempHtmlFile}");
                await page.WaitForSelectorAsync(".mermaid"); // Wait for Mermaid to render
                await page.ScreenshotAsync(outputFilePath, new ScreenshotOptions { FullPage = true });
            }
        }
        catch (IOException ex)
        {
            throw new IOException("An error occurred while accessing the file.", ex);
        }
        catch (Exception ex) // Catch any other exceptions that might occur  
        {
            throw new InvalidOperationException(
                "An unexpected error occurred during the Mermaid diagram rendering.", ex);
        }
        finally
        {
            // Clean up the temporary HTML file  
            if (File.Exists(tempHtmlFile))
            {
                File.Delete(tempHtmlFile);
            }
        }

        return outputFilePath;
    }
}
