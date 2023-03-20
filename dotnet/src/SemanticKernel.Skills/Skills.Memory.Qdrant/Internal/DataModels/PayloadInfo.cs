// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

internal class PayloadInfo
{
    [JsonPropertyName("data_type")]
    internal string? PayloadDataType { get; set; }
    
    [JsonPropertyName("params")]
    internal PayloadParams? PayloadParams { get; set; }

    [JsonPropertyName("points")]
    internal int NumOfPoints {get; set;}

}

internal class PayloadParams
{
    [JsonPropertyName("type")]
    internal string? PayloadType { get; set; }
    [JsonPropertyName("tokenizer")]
    internal string? Tokenizer { get; set; }
    [JsonPropertyName("min_token_len")]
    internal int MinTokenLen { get; set; }
    [JsonPropertyName("max_token_len")]
    internal int MaxTokenLen { get; set; }
    [JsonPropertyName("lowercase")]
    internal bool Lowercase { get; set; }

}
internal enum PayloadTypes
{
    Keyword,
    Integer, 
    Float, 
    Geo, 
    Text
}
