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
    /// <param name="filename"></param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static async Task GenerateMermaidImageAsync(string mermaidCode, string filename)
    {
        // Locate the current assembly's directory
        string? assemblyPath = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (assemblyPath == null)
        {
            throw new InvalidOperationException("Could not determine the assembly path.");
        }

        // Define the output folder path and create it if it doesn't exist
        string outputPath = Path.Combine(assemblyPath, "output");
        Directory.CreateDirectory(outputPath);

        // Full path for the output file
        string outputFilePath = Path.Combine(outputPath, filename);

        // Download Chromium if it hasn't been installed yet
        BrowserFetcher browserFetcher = new();
        browserFetcher.Browser = SupportedBrowser.Chrome;
        await browserFetcher.DownloadAsync();
        //await new BrowserFetcher().DownloadAsync(BrowserFetcher.DefaultChromiumRevision);

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
        await File.WriteAllTextAsync(tempHtmlFile, htmlContent);

        // Launch Puppeteer-Sharp with a headless browser to render the Mermaid diagram
        using (var browser = await Puppeteer.LaunchAsync(new LaunchOptions { Headless = true }))
        using (var page = await browser.NewPageAsync())
        {
            await page.GoToAsync($"file://{tempHtmlFile}");
            await page.WaitForSelectorAsync(".mermaid"); // Wait for Mermaid to render
            await page.ScreenshotAsync(outputFilePath, new ScreenshotOptions { FullPage = true });
        }

        // Clean up the temporary HTML file
        File.Delete(tempHtmlFile);
        Console.WriteLine($"Diagram generated at: {outputFilePath}");
    }
}
