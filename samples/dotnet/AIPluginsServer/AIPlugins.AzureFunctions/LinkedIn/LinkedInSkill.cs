using System;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using AIPlugins.AzureFunctions.LinkedIn.Models;
using Microsoft.SemanticKernel.SkillDefinition;

namespace AIPlugins.AzureFunctions.LinkedIn;

public class LinkedInSkill
{
    private static readonly Uri GetProfileUri = new("https://api.linkedin.com/v2/me");
    private static readonly Uri PostContentUri = new("https://api.linkedin.com/v2/ugcPosts");
    private static readonly Uri RegisterUploadUri = new("https://api.linkedin.com/v2/assets?action=registerUpload");

    public static class Parameters
    {
        public const string AuthToken = "authToken";

        public const string PersonURN = "personURN";

        public const string ImagePath = "imagePath";

        public const string Image = "image";

        public const string ImageAsset = "imageAsset";

        public const string ArticleUri = "articleUri";
    }

    [SKFunction, Description("Gets my LinkedIn User ID (UPN)")]
    public async Task<string> GetPersonUpnAsync(
        [Description("The authToken of the user to get the UPN for")] string authToken,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(authToken))
        {
            throw new ArgumentNullException(nameof(authToken));
        }

        using (var httpClient = new HttpClient())
        {
            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");

            var profileString = await httpClient.GetStringAsync(GetProfileUri,
                cancellationToken).ConfigureAwait(false);

            var profile = JsonSerializer.Deserialize<ProfileResponse>(
                profileString,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (profile == null)
            {
                throw new JsonException("Could not parse profile response");
            }

            return profile.Id;
        }
    }

    [SKFunction, Description("Uploads an image to LinkedIn for use in a post")]
    public async Task UploadImageAsync(
        [Description("The authToken of the user to get the UPN for")] string authToken,
        [Description("The local filepath of the image to upload")] string imagePath,
        [Description("The unique person identifier to associate with the image")] string personId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(authToken)) { throw new ArgumentNullException(nameof(authToken)); }
        if (string.IsNullOrEmpty(imagePath)) { throw new ArgumentNullException(nameof(imagePath)); }
        if (string.IsNullOrEmpty(personId)) { throw new ArgumentNullException(nameof(personId)); }

        using (var httpClient = new HttpClient())
        {
            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            var regImgUpload = new RegisterRequest();
            regImgUpload.RegisterUploadRequest.Owner = $"urn:li:person:{personId}";

            var json = JsonSerializer.Serialize(regImgUpload,
                new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase});
            using var requestContent = new StringContent(json);

            var response = await httpClient.PostAsync(RegisterUploadUri,
                requestContent,
                cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var content = await response.Content
                .ReadAsStringAsync(cancellationToken)
                .ConfigureAwait(false);

            var registerResponse = JsonSerializer.Deserialize<RegisterResponse>(content, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (registerResponse == null) { throw new JsonException($"Could not parse json response from call to {RegisterUploadUri}"); }

            using (var fs = System.IO.File.OpenRead(imagePath))
            {
                var uploadUrl = registerResponse.Value.UploadMechanism.Request.UploadUrl;
                using StreamContent stream = new(fs);
                var uploadResponse = await httpClient.PostAsync(uploadUrl,
                    stream,
                    cancellationToken).ConfigureAwait(false);
                uploadResponse.EnsureSuccessStatusCode();
            }
        }
    }

    [SKFunction, Description("Posts an article to LinkedIn")]
    public async Task PostArticleAsync(
        [Description("The text comment to post along with the article.")] string input,
        [Description("The authToken of the user")] string authToken,
        [Description("The URI of the article to post")] string articleUri,
        [Description("The unique person identifier to associate with the article")] string personId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(input)) { throw new ArgumentNullException(nameof(input)); }
        if (string.IsNullOrEmpty(authToken)) { throw new ArgumentNullException(nameof(authToken)); }
        if (string.IsNullOrEmpty(articleUri)) { throw new ArgumentNullException(nameof(articleUri)); }
        if (string.IsNullOrEmpty(personId)) { throw new ArgumentNullException(nameof(personId)); }

        using (var httpClient = new HttpClient())
        {
            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            dynamic json = new
            {
                author = $"urn:li:person:{personId}",
                lifecycleState = "PUBLISHED",
                specificContent = new SpecificContent
                {
                    ShareContent = new
                    {
                        shareCommentary = new
                        {
                            text = input
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
            using var requestContent = new StringContent(jsonString);

            var response = await httpClient.PostAsync(PostContentUri,
                requestContent,
                cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
        }
    }

    [SKFunction, Description("Posts content to LinkedIn")]
    public async Task PostContentAsync(
        [Description("The text comment to post.")] string input,
        [Description("The authToken of the user")] string authToken,
        [Description("The unique person identifier to associate with the image")] string personId,
        [Description("The image asset id that should be included in the post (optional)")] string? imageAssetId,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(input)) { throw new ArgumentNullException(nameof(input)); }
        if (string.IsNullOrEmpty(authToken)) { throw new ArgumentNullException(nameof(authToken)); }
        if (string.IsNullOrEmpty(personId)) { throw new ArgumentNullException(nameof(personId)); }

        using (var httpClient = new HttpClient())
        {
            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            dynamic json = new
            {
                author = $"urn:li:person:{personId}",
                lifecycleState = "PUBLISHED",
                specificContent = new SpecificContent
                {
                    ShareContent = new
                    {
                        shareCommentary = new
                        {
                            text = input
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
            using var requestContent = new StringContent(jsonString);
            var response = await httpClient.PostAsync(PostContentUri,
                requestContent,
                cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
        }
    }

    [SKFunction, Description("Uploads an image to LinkedIn for use in a post")]
     public async Task<string> UploadImageV2Async(
        [Description("The text comment to post.")] string input,
        [Description("The authToken of the user")] string authToken,
        [Description("The unique person identifier to associate with the image")] string personId,
        [Description("The content of the image to upload, as a base64-encoded string")] string imageBase64,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(input)) { throw new ArgumentNullException(nameof(input)); }
        if (string.IsNullOrEmpty(authToken)) { throw new ArgumentNullException(nameof(authToken)); }
        if (string.IsNullOrEmpty(personId)) { throw new ArgumentNullException(nameof(personId)); }
        if (string.IsNullOrEmpty(imageBase64)) { throw new ArgumentNullException(nameof(imageBase64)); }

        using (var httpClient = new HttpClient())
        {
            httpClient.DefaultRequestHeaders.Add("authorization", $"Bearer {authToken}");
            httpClient.DefaultRequestHeaders.Add("X-Restli-Protocol-Version", "2.0.0");

            var regImgUpload = new RegisterRequest();
            regImgUpload.RegisterUploadRequest.Owner = $"urn:li:person:{personId}";
            using var regImgRequestContent = new StringContent(
                JsonSerializer.Serialize(regImgUpload,
                    new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));

            var response = await httpClient.PostAsync(RegisterUploadUri,
                regImgRequestContent,
                cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

            var registerResponse = JsonSerializer.Deserialize<RegisterResponse>(
                content,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (registerResponse == null) { throw new JsonException($"Could not parse json response from call to {RegisterUploadUri}"); }

            var bytes = Convert.FromBase64String(imageBase64);
            using var imageContent = new StreamContent(new MemoryStream(bytes));

            var uploadResponse = await httpClient.PostAsync(
                registerResponse.Value.UploadMechanism.Request.UploadUrl,
                imageContent,
                cancellationToken).ConfigureAwait(false);

            uploadResponse.EnsureSuccessStatusCode();

            return registerResponse.Value.Asset;
        }
    }
}
