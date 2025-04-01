// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;
#pragma warning disable CA1812 // Instantiated by reflection
/// <summary>
/// Brave search response.
/// </summary>
//https://api.search.brave.com/res/v1/web/search
//https://api.search.brave.com/res/v1/local/pois local wis
//https://api.search.brave.com/res/v1/local/descriptions
public sealed class BraveSearchResponse<T>
{
        [JsonPropertyName("query")]
        public BraveQuery query { get; set; }

        [JsonPropertyName("mixed")]
        public Mixed mixed { get; set; }

        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("videos")]
        public BraveVideos videos  { get;set; }

        [JsonPropertyName("web")]
        public BraveWeb web { get; set; }
}

// var myDeserializedClass = JsonSerializer.Deserialize<BraveSearchResponse<T>>(myJsonResponse);
    public sealed class Button
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("title")]
        public string title { get; set; }

        [JsonPropertyName("url")]
        public string url { get; set; }
    }

    public class DeepResults
    {
        [JsonPropertyName("buttons")]
        public List<Button> buttons { get; set; }
    }

    public class Main
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("index")]
        public int? index { get; set; }

        [JsonPropertyName("all")]
        public bool? all { get; set; }
    }

    public class MetaUrl
    {
        [JsonPropertyName("scheme")]
        public string scheme { get; set; }

        [JsonPropertyName("netloc")]
        public string netloc { get; set; }

        [JsonPropertyName("hostname")]
        public string hostname { get; set; }

        [JsonPropertyName("favicon")]
        public string favicon { get; set; }

        [JsonPropertyName("path")]
        public string path { get; set; }
    }

    public sealed class Mixed
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("main")]
        public List<Main> main { get; set; }

        [JsonPropertyName("top")]
        public List<object> top { get; set; }

        [JsonPropertyName("side")]
        public List<object> side { get; set; }
    }

    public sealed class Profile
    {
        [JsonPropertyName("name")]
        public string name { get; set; }

        [JsonPropertyName("url")]
        public string url { get; set; }

        [JsonPropertyName("long_name")]
        public string long_name { get; set; }

        [JsonPropertyName("img")]
        public string img { get; set; }
    }

    public sealed class BraveQuery
    {
        [JsonPropertyName("original")]
        public string original { get; set; }

        [JsonPropertyName("show_strict_warning")]
        public bool? show_strict_warning { get; set; }

        [JsonPropertyName("is_navigational")]
        public bool? is_navigational { get; set; }

        [JsonPropertyName("is_news_breaking")]
        public bool? is_news_breaking { get; set; }

        [JsonPropertyName("spellcheck_off")]
        public bool? spellcheck_off { get; set; }

        [JsonPropertyName("country")]
        public string country { get; set; }

        [JsonPropertyName("bad_results")]
        public bool? bad_results { get; set; }

        [JsonPropertyName("should_fallback")]
        public bool? should_fallback { get; set; }

        [JsonPropertyName("postal_code")]
        public string postal_code { get; set; }

        [JsonPropertyName("city")]
        public string city { get; set; }

        [JsonPropertyName("header_country")]
        public string header_country { get; set; }

        [JsonPropertyName("more_results_available")]
        public bool? more_results_available { get; set; }

        [JsonPropertyName("state")]
        public string state { get; set; }
    }

    public sealed class BraveWebResult
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("url")]
        public string url { get; set; }

        [JsonPropertyName("title")]
        public string title { get; set; }

        [JsonPropertyName("description")]
        public string description { get; set; }

        [JsonPropertyName("age")]
        public string age { get; set; }

        [JsonPropertyName("page_age")]
        public DateTime? page_age { get; set; }

        [JsonPropertyName("video")]
        public BraveVideo video { get; set; }

        [JsonPropertyName("meta_url")]
        public MetaUrl meta_url { get; set; }

        [JsonPropertyName("thumbnail")]
        public Thumbnail thumbnail { get; set; }

        [JsonPropertyName("is_source_local")]
        public bool? is_source_local { get; set; }

        [JsonPropertyName("is_source_both")]
        public bool? is_source_both { get; set; }

        [JsonPropertyName("profile")]
        public Profile profile { get; set; }

        [JsonPropertyName("language")]
        public string language { get; set; }

        [JsonPropertyName("family_friendly")]
        public bool? family_friendly { get; set; }

        [JsonPropertyName("subtype")]
        public string subtype { get; set; }

        [JsonPropertyName("is_live")]
        public bool? is_live { get; set; }

        [JsonPropertyName("deep_results")]
        public DeepResults deep_results { get; set; }
    }


    public class Thumbnail
    {
        [JsonPropertyName("src")]
        public string src { get; set; }

        [JsonPropertyName("original")]
        public string original { get; set; }

        [JsonPropertyName("logo")]
        public bool? logo { get; set; }
    }

    public sealed class BraveVideo
    {
        [JsonPropertyName("duration")]
        public string duration { get; set; }

        [JsonPropertyName("views")]
        public int? views { get; set; }

        [JsonPropertyName("creator")]
        public string creator { get; set; }

        [JsonPropertyName("publisher")]
        public string publisher { get; set; }
    }

    public sealed class BraveVideos
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        [JsonPropertyName("results")]
        public List<BraveWebResult> results { get; set; }

        [JsonPropertyName("mutated_by_goggles")]
        public bool? mutated_by_goggles { get; set; }
    }

    public sealed  class BraveWeb
    {
        [JsonPropertyName("type")]
        public string type { get; set; }

        // T BraveWebResult
        [JsonPropertyName("results")]
        public List<BraveWebResult> results { get; set; }

        [JsonPropertyName("family_friendly")]
        public bool? family_friendly { get; set; }
    }


