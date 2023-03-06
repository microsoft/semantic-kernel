// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Qdrant.DotNet.Internal.Diagnostics;

namespace Qdrant.DotNet.Internal.Http.Specs;

internal class FetchVectorsResponse 
{ 
    internal class Points
    {   
        [JsonPropertyName("id")]
        internal string? VectorId {get; set; }

        [JsonPropertyName("payload")]
        internal Dictionary<string, object>? Payload { get; set; }
        
        [JsonPropertyName("vector")]
        internal float[]? Vector { get; set; }

        internal Points()
        {}
    }
      
    internal string Status { get; set; }
    internal List<Points> VectorPointCollection { get; set; }

    internal void ConvertFromJson(string json)
    {
        try 
        {
            JsonNode jsondata  = JsonNode.Parse(json)!;
        
            this.Status = jsondata.Root["status"]!.GetValue<string>()!;
            JsonNode result = jsondata.Root["result"]!;

            foreach (JsonNode? point in result.Root["points"]!.AsArray())
            {
                Points newPoint = new Points();
                newPoint = point.Deserialize<Points>()!;
                this.VectorPointCollection.Add(newPoint);
            }
        }
        catch (Exception ex)
        {
            throw new JsonException("Error in parsing Json from retrieving vectors", ex);
        }

    }

    internal FetchVectorsResponse(string json) : this()
    {
        this.ConvertFromJson(json);
    }

    #region private ================================================================================

    private FetchVectorsResponse()
    {
        this.Status = "";
        this.VectorPointCollection = new List<Points>();
    }

    #endregion
}