// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;

namespace AIPlugins.AzureFunctions;
public class PostModel
{
    [Required]
    [OpenApiProperty(Description = "Content to share.")]
    public string Text { get; set; }

    [Required]
    [OpenApiProperty(Description = "Content image url.")]
    public string ImageUrl { get; set; }
}
