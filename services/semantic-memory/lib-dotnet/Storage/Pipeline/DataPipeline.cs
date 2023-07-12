// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Internal;
using Microsoft.SemanticKernel.Services.Diagnostics;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

/// <summary>
/// DataPipeline representation.
/// Note: this object could be generalized to support any kind of pipeline, for now it's tailored
///       to specific design of SK memory indexer. You can use 'CustomData' to extend the logic.
/// </summary>
public class DataPipeline
{
    public class FileDetails
    {
        [JsonPropertyOrder(1)]
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyOrder(2)]
        [JsonPropertyName("size")]
        public long Size { get; set; } = 0;

        [JsonPropertyOrder(3)]
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyOrder(4)]
        [JsonPropertyName("fulltext_file")]
        public string FullTextFile { get; set; } = string.Empty;

        [JsonPropertyOrder(5)]
        [JsonPropertyName("generated_files")]
        public HashSet<string> GeneratedFiles { get; set; } = new();
    }

    /// <summary>
    /// Id of the pipeline instance. This value will persist throughout the execution and in the final data lineage used for citations.
    /// </summary>
    [JsonPropertyOrder(1)]
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Full list of the steps in this pipeline.
    /// </summary>
    [JsonPropertyOrder(2)]
    [JsonPropertyName("steps")]
    public List<string> Steps { get; set; } = new();

    /// <summary>
    /// List of the steps remaining.
    /// </summary>
    [JsonPropertyOrder(3)]
    [JsonPropertyName("remaining_steps")]
    public List<string> RemainingSteps { get; set; } = new();

    /// <summary>
    /// List of steps already completed.
    /// </summary>
    [JsonPropertyOrder(4)]
    [JsonPropertyName("completed_steps")]
    public List<string> CompletedSteps { get; set; } = new();

    [JsonPropertyOrder(5)]
    [JsonPropertyName("user_id")]
    public string UserId { get; set; } = string.Empty;

    [JsonPropertyOrder(6)]
    [JsonPropertyName("vaults")]
    public List<string> VaultIds { get; set; } = new();

    [JsonPropertyOrder(7)]
    [JsonPropertyName("creation")]
    public DateTimeOffset Creation { get; set; }

    [JsonPropertyOrder(8)]
    [JsonPropertyName("last_update")]
    public DateTimeOffset LastUpdate { get; set; }

    [JsonPropertyOrder(9)]
    [JsonPropertyName("files")]
    public List<FileDetails> Files { get; set; } = new();

    /// <summary>
    /// Unstructured dictionary available to support custom tasks and business logic.
    /// The orchestrator doesn't use this property, and it's up to custom handlers to manage it.
    /// </summary>
    [JsonPropertyOrder(10)]
    [JsonPropertyName("custom_data")]
    public Dictionary<string, object> CustomData { get; set; } = new();

    [JsonIgnore]
    public bool Complete => this.RemainingSteps.Count == 0;

    [JsonIgnore]
    public List<IFormFile> FilesToUpload { get; set; } = new();

    [JsonIgnore]
    public bool UploadComplete { get; set; }

    public DataPipeline Then(string stepName)
    {
        this.Steps.Add(stepName);
        return this;
    }

    public DataPipeline AddUploadFile(string name, string filename, string sourceFile)
    {
        return this.AddUploadFile(name, filename, File.ReadAllBytes(sourceFile));
    }

    public DataPipeline AddUploadFile(string name, string filename, byte[] content)
    {
        return this.AddUploadFile(name, filename, new BinaryData(content));
    }

    public DataPipeline AddUploadFile(string name, string filename, BinaryData content)
    {
        return this.AddUploadFile(name, filename, content.ToStream());
    }

    public DataPipeline AddUploadFile(string name, string filename, Stream content)
    {
        content.Seek(0, SeekOrigin.Begin);
        this.FilesToUpload.Add(new FormFile(content, 0, content.Length, name, filename));
        return this;
    }

    public DataPipeline Build()
    {
        if (this.FilesToUpload.Count > 0)
        {
            this.UploadComplete = false;
        }

        this.RemainingSteps = this.Steps.Select(x => x).ToList();
        this.Creation = DateTimeOffset.UtcNow;
        this.LastUpdate = this.Creation;

        return this;
    }

    /// <summary>
    /// Change the pipeline to the next step, returning the name of the next step to execute.
    /// The name returned is used to choose the queue where the pipeline will be set.
    /// </summary>
    /// <returns></returns>
    /// <exception cref="IndexOutOfRangeException"></exception>
    public string MoveToNextStep()
    {
        if (this.RemainingSteps.Count == 0)
        {
            throw new PipelineCompletedException("The list of remaining steps is empty");
        }

        var stepName = this.RemainingSteps.First();
        this.RemainingSteps = this.RemainingSteps.GetRange(1, this.RemainingSteps.Count - 1);
        this.CompletedSteps.Add(stepName);

        return stepName;
    }

    public void Validate()
    {
        if (string.IsNullOrEmpty(this.Id))
        {
            throw new ArgumentException("The pipeline ID is empty", nameof(this.Id));
        }

        if (string.IsNullOrEmpty(this.UserId))
        {
            throw new ArgumentException("The user ID is empty", nameof(this.UserId));
        }

        string previous = string.Empty;
        foreach (string step in this.Steps)
        {
            if (string.IsNullOrEmpty(step))
            {
                throw new ArgumentException("The pipeline contains a step with empty name", nameof(this.Steps));
            }

            // This scenario is not allowed, to ensure execution consistency
            if (string.Compare(step, previous, StringComparison.InvariantCultureIgnoreCase) == 0)
            {
                throw new ArgumentException("The pipeline contains two consecutive steps with the same name", nameof(this.Steps));
            }

            previous = step;
        }
    }
}
