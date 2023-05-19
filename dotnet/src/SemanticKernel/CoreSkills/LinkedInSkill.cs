using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

public class LinkedInSkill
{
    public static class Parameters
    {
        public const string AuthToken = "authToken";

        public const string PersonURN = "personURN";

        public const string ImagePath = "imagePath";

        public const string Image = "image";

        public const string ImageAsset = "imageAsset";

        public const string ArticleUri = "articleUri";
    }

    [SKFunction("Gets my UPN")]
    [SKFunctionName("GetPersonUpn")]
    [SKFunctionInput(Description = "Gets my LinkedIn UPN")]
    [SKFunctionContextParameter(Name = Parameters.AuthToken, Description = "The authToken of the user to get the UPN for")]
    public async Task<string> GetPersonUpnAsync(string source, SKContext context)
    {
        using (var httpClient = new HttpClient())
        {
            if (!context.Variables.Get(Parameters.AuthToken, out string authToken) || string.IsNullOrEmpty(authToken))
            {
                throw new Exception("Missing auth token");
            }

            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");

            var profileString = await httpClient.GetStringAsync("https://api.linkedin.com/v2/me").ConfigureAwait(false);

            var profile = JsonSerializer.Deserialize<ProfileResponse>(profileString, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            return profile.Id;
        }
    }

    [SKFunction("Uploads an image to LinkedIn for use in a post")]
    [SKFunctionName("UploadImage")]
    [SKFunctionContextParameter(Name = Parameters.AuthToken, Description = "The authToken of the user to get the profile for")]
    [SKFunctionContextParameter(Name = Parameters.ImagePath, Description = "The path of the image to upload")]
    [SKFunctionContextParameter(Name = Parameters.PersonURN, Description = "The unique person identifier to associate with the image")]
    public async Task<string> UploadImageAsync(string source, SKContext context)
    {
        using (var httpClient = new HttpClient())
        {
            if (!context.Variables.Get(Parameters.AuthToken, out string authToken) || string.IsNullOrEmpty(authToken))
            {
                throw new Exception("Missing auth token");
            }

            if (!context.Variables.Get(Parameters.PersonURN, out string personUrn) || string.IsNullOrEmpty(personUrn))
            {
                throw new Exception("Missing person URN");
            }

            if (!context.Variables.Get(Parameters.ImagePath, out string imgPath) || string.IsNullOrEmpty(imgPath))
            {
                throw new Exception("Missing path to image");
            }

            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            var regImgUpload = new RegisterRequest();
            regImgUpload.RegisterUploadRequest.Owner = $"urn:li:person:{personUrn}";

            var response = await httpClient.PostAsync("https://api.linkedin.com/v2/assets?action=registerUpload",
                new StringContent(JsonSerializer.Serialize(regImgUpload,
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    }))).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var registerResponse = JsonSerializer.Deserialize<RegisterResponse>(content, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            using (var fs = System.IO.File.OpenRead(imgPath))
            {
                var uploadResponse = await httpClient.PostAsync(registerResponse.Value.UploadMechanism.Request.UploadUrl, new StreamContent(fs)).ConfigureAwait(false);
                uploadResponse.EnsureSuccessStatusCode();
            }

            return registerResponse.Value.Asset;
        }
    }

    [SKFunction("Posts an article to LinkedIn")]
    [SKFunctionName("PostArticle")]
    [SKFunctionContextParameter(Name = Parameters.AuthToken, Description = "The authToken of the user to get the profile for")]
    [SKFunctionContextParameter(Name = Parameters.ArticleUri, Description = "The URI of the article")]
    [SKFunctionContextParameter(Name = Parameters.PersonURN, Description = "The unique person identifier to associate with the image")]
    public async Task PostArticleAsync(string source, SKContext context)
    {
        using (var httpClient = new HttpClient())
        {
            if (!context.Variables.Get(Parameters.AuthToken, out string authToken) || string.IsNullOrEmpty(authToken))
            {
                throw new Exception("Missing auth token");
            }

            if (!context.Variables.Get(Parameters.PersonURN, out string personUrn) || string.IsNullOrEmpty(personUrn))
            {
                throw new Exception("Missing person URN");
            }

            if (!context.Variables.Get(Parameters.ArticleUri, out string articleUri) || string.IsNullOrEmpty(articleUri))
            {
                throw new Exception("Missing article URI");
            }

            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            dynamic json = new
            {
                author = $"urn:li:person:{personUrn}",
                lifecycleState = "PUBLISHED",
                specificContent = new SpecificContent
                {
                    ShareContent = new
                    {
                        shareCommentary = new
                        {
                            text = source
                        },
                        shareMediaCategory = "ARTICLE",
                        media = new[]
                        {
                            new
                            {
                                status= "READY",
                                originalUrl= articleUri
                            }
                        }
                    }
                },
                visibility = new PublicNetworkVisibility()
            };

            var jsonString = JsonSerializer.Serialize(json);

            var response = await httpClient.PostAsync("https://api.linkedin.com/v2/ugcPosts", new StringContent(jsonString)).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
        }
    }

    [SKFunction("Posts content to LinkedIn")]
    [SKFunctionName("PostContent")]
    [SKFunctionContextParameter(Name = Parameters.AuthToken, Description = "The authToken of the user to get the profile for")]
    [SKFunctionContextParameter(Name = Parameters.ImageAsset, Description = "The image asset id that should be included in the post")]
    [SKFunctionContextParameter(Name = Parameters.PersonURN, Description = "The unique person identifier to associate with the image")]
    public async Task PostContentAsync(string source, SKContext context)
    {
        using (var httpClient = new HttpClient())
        {
            if (!context.Variables.Get(Parameters.AuthToken, out string authToken) || string.IsNullOrEmpty(authToken))
            {
                throw new Exception("Missing auth token");
            }

            if (!context.Variables.Get(Parameters.PersonURN, out string personUrn) || string.IsNullOrEmpty(personUrn))
            {
                throw new Exception("Missing person URN");
            }

            context.Variables.Get(Parameters.ImageAsset, out string imageAssetId);

            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            dynamic json = new
            {
                author = $"urn:li:person:{personUrn}",
                lifecycleState = "PUBLISHED",
                specificContent = new SpecificContent
                {
                    ShareContent = new
                    {
                        shareCommentary = new
                        {
                            text = source
                        },
                        shareMediaCategory = string.IsNullOrEmpty(imageAssetId) ? "NONE" : "IMAGE",
                        media = new[]
                        {
                            new
                            {
                                status= "READY",
                                media = imageAssetId
                            }
                        }
                    }
                },
                visibility = new PublicNetworkVisibility()
            };

            var jsonString = JsonSerializer.Serialize(json);

            var response = await httpClient.PostAsync("https://api.linkedin.com/v2/ugcPosts", new StringContent(jsonString)).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
        }
    }

    [SKFunction("Uploads an image to LinkedIn for use in a post")]
    [SKFunctionName("UploadImageV2")]
    [SKFunctionContextParameter(Name = Parameters.AuthToken, Description = "The authToken of the user to get the profile for")]
    [SKFunctionContextParameter(Name = Parameters.Image, Description = "The content of the image to upload")]
    [SKFunctionContextParameter(Name = Parameters.PersonURN, Description = "The unique person identifier to associate with the image")]
    public async Task<string> UploadImageV2Async(string source, SKContext context)
    {
        using (var httpClient = new HttpClient())
        {
            if (!context.Variables.Get(Parameters.AuthToken, out string authToken) || string.IsNullOrEmpty(authToken))
            {
                throw new Exception("Missing auth token");
            }

            if (!context.Variables.Get(Parameters.PersonURN, out string personUrn) || string.IsNullOrEmpty(personUrn))
            {
                throw new Exception("Missing person URN");
            }

            if (!context.Variables.Get(Parameters.Image, out string imgContent) || string.IsNullOrEmpty(imgContent))
            {
                throw new Exception("Missing image content");
            }

            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            var regImgUpload = new RegisterRequest();
            regImgUpload.RegisterUploadRequest.Owner = $"urn:li:person:{personUrn}";

            var response = await httpClient.PostAsync("https://api.linkedin.com/v2/assets?action=registerUpload",
                new StringContent(JsonSerializer.Serialize(regImgUpload,
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    }))).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            var registerResponse = JsonSerializer.Deserialize<RegisterResponse>(content, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            var bytes = Convert.FromBase64String(imgContent);

            var uploadResponse = await httpClient.PostAsync(registerResponse.Value.UploadMechanism.Request.UploadUrl, new StreamContent(new MemoryStream(bytes))).ConfigureAwait(false);

            uploadResponse.EnsureSuccessStatusCode();

            return registerResponse.Value.Asset;
        }
    }
}


#region LinkedIn Models
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

    public string UploadUrl { get; set; } = string.Empty;
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
#endregion
