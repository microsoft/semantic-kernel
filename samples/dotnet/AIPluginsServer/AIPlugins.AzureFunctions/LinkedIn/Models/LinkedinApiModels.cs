// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace AIPlugins.AzureFunctions.LinkedIn.Models;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.

public class PublicNetworkVisibility
{
    [JsonPropertyName("com.linkedin.ugc.MemberNetworkVisibility")]
    public string Visibility { get; set; } = "PUBLIC";
}

public class SpecificContent
{
    [JsonPropertyName("com.linkedin.ugc.ShareContent")]
    public object ShareContent { get; set; }
}

public class ProfileResponse
{
    public string Id { get; set; }
}

public class RegisterResponse
{
    public RegisterResponseItem Value { get; set; } = new RegisterResponseItem();
}

public class RegisterResponseItem
{
    public string Asset { get; set; } = string.Empty;
    public string MediaArtifact { get; set; } = string.Empty;

    public UploadMechanism UploadMechanism { get; set; } = new UploadMechanism();
}

public class MediaUploadHttpRequest
{
    //also has a headers object that we'll ignore

    public Uri UploadUrl { get; set; }
}

public class UploadMechanism
{
    [JsonPropertyName("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest")]
    public MediaUploadHttpRequest Request { get; set; }
}

public class RegisterRequest
{
    public RegisterUploadRequestItem RegisterUploadRequest { get; set; } = new();
}

public class RegisterUploadRequestItem
{
    public List<string> Recipes { get; set; } = new List<string>() { "urn:li:digitalmediaRecipe:feedshare-image" };
    public string Owner { get; set; } = string.Empty;
    public List<ServiceRelationships> ServiceRelationships { get; set; } = new List<ServiceRelationships> { new ServiceRelationships { RelationshipType = "OWNER", Identifier = "urn:li:userGeneratedContent" } };
}

public class ServiceRelationships
{
    public string RelationshipType { get; set; } = string.Empty;
    public string Identifier { get; set; } = string.Empty;
}

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
