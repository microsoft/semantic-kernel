// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal class PromptyChatParser
{
    private string _path;
    public PromptyChatParser(Prompty prompty)
    {
        this._path = prompty.FilePath;
    }

    public string InlineImage(string imageItem)
    {
        // Pass through if it's a URL or base64 encoded
        if (imageItem.StartsWith("http") || imageItem.StartsWith("data"))
        {
            return imageItem;
        }
        // Otherwise, it's a local file - need to base64 encode it
        else
        {
            string imageFilePath = Path.Combine(this._path, imageItem);
            byte[] imageBytes = File.ReadAllBytes(imageFilePath);
            string base64Image = Convert.ToBase64String(imageBytes);

            if (Path.GetExtension(imageFilePath).Equals(".png", StringComparison.OrdinalIgnoreCase))
            {
                return $"data:image/png;base64,{base64Image}";
            }
            else if (Path.GetExtension(imageFilePath).Equals(".jpg", StringComparison.OrdinalIgnoreCase) ||
                     Path.GetExtension(imageFilePath).Equals(".jpeg", StringComparison.OrdinalIgnoreCase))
            {
                return $"data:image/jpeg;base64,{base64Image}";
            }
            else
            {
                throw new ArgumentException($"Invalid image format {Path.GetExtension(imageFilePath)}. " +
                                            "Currently only .png and .jpg / .jpeg are supported.");
            }
        }
    }

    public List<Dictionary<string, string>> ParseContent(string content)
    {
        // Regular expression to parse markdown images
        // var imagePattern = @"(?P<alt>!\[[^\]]*\])\((?P<filename>.*?)(?=""|\))";
        var imagePattern = @"(\!\[[^\]]*\])\(([^""\)]+)(?=\""\))";
        var matches = Regex.Matches(content, imagePattern, RegexOptions.Multiline);

        if (matches.Count > 0)
        {
            var contentItems = new List<Dictionary<string, string>>();
            var contentChunks = Regex.Split(content, imagePattern, RegexOptions.Multiline);
            var currentChunk = 0;

            for (int i = 0; i < contentChunks.Length; i++)
            {
                // Image entry
                if (currentChunk < matches.Count && contentChunks[i] == matches[currentChunk].Groups[0].Value)
                {
                    contentItems.Add(new Dictionary<string, string>
                {
                    { "type", "image_url" },
                    { "image_url", this.InlineImage(matches[currentChunk].Groups[2].Value.Split([" "], StringSplitOptions.None)[0].Trim()) }
                });
                }
                // Second part of image entry
                else if (currentChunk < matches.Count && contentChunks[i] == matches[currentChunk].Groups[2].Value)
                {
                    currentChunk++;
                }
                // Text entry
                else
                {
                    var trimmedChunk = contentChunks[i].Trim();
                    if (!string.IsNullOrEmpty(trimmedChunk))
                    {
                        contentItems.Add(new Dictionary<string, string>
                    {
                        { "type", "text" },
                        { "text", trimmedChunk }
                    });
                    }
                }
            }

            return contentItems;
        }
        else
        {
            // No image matches found, return original content
            return new List<Dictionary<string, string>>
            {
                new Dictionary<string, string>
                {
                    { "type", "text" },
                    { "text", content }
                }
            };
        }
    }



    public Prompty ParseTemplate(Prompty data)
    {
        var roles = (RoleType[])Enum.GetValues(typeof(RoleType));
        var messages = new List<Dictionary<string, string>>();
        var separator = @"(?i)^\s*#?\s*(" + string.Join("|", roles) + @")\s*:\s*\n";

        // Get valid chunks - remove empty items
        var chunks = new List<string>();
        foreach (var item in Regex.Split(data.Prompt, separator, RegexOptions.Multiline))
        {
            if (!string.IsNullOrWhiteSpace(item))
            {
                chunks.Add(item.Trim());
            }
        }

        // If no starter role, then inject system role
        if (!chunks[0].ToLower().Trim().Equals(RoleType.system.ToString().ToLower()))
        {
            chunks.Insert(0, RoleType.system.ToString());
        }

        // If last chunk is role entry, then remove (no content?)
        if (chunks[chunks.Count - 1].ToLower().Trim().Equals(RoleType.system.ToString().ToLower()))
        {
            chunks.RemoveAt(chunks.Count - 1);
        }

        if (chunks.Count % 2 != 0)
        {
            throw new ArgumentException("Invalid prompt format");
        }

        // Create messages
        for (int i = 0; i < chunks.Count; i += 2)
        {
            var role = chunks[i].ToLower().Trim();
            var content = chunks[i + 1].Trim();
            var parsedContent = this.ParseContent(content).LastOrDefault().Values.LastOrDefault();
            messages.Add(new Dictionary<string, string> { { "role", role }, { "content", parsedContent } });
        }
        data.Messages = messages;

        return data;
    }
}

