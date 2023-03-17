// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class FetchVectorsResponse
{

    
    internal List<Points> VectorPointCollection { get; set; }

    internal void ConvertFromJson(string json)
    {
        try
        {
            JsonNode jsondata = JsonNode.Parse(json)!;

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
