// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

/// <summary>
/// Azure OpenAI deployment schema
/// </summary>
public sealed class AzureDeployments
{
    /// <summary>
    /// An Azure OpenAI deployment
    /// </summary>
    public class AzureDeployment
    {
        private string _status = string.Empty;
        private string _type = string.Empty;

        /// <summary>
        /// Azure deployment name
        /// </summary>
        [JsonPropertyName("id")]
        public string DeploymentName { get; set; } = string.Empty;

        /// <summary>
        /// Model Name
        /// </summary>
        [JsonPropertyName("model")]
        public string ModelName { get; set; } = string.Empty;

        /// <summary>
        /// Status of the deployment
        /// </summary>
        [JsonPropertyName("status")]
        [SuppressMessage("Globalization", "CA1308:Normalize strings to uppercase", Justification = "Azure API expects lowercase")]
        public string Status
        {
            get => this._status;
            // ReSharper disable once ConditionalAccessQualifierIsNonNullableAccordingToAPIContract
            set => this._status = value?.ToLowerInvariant().Trim() ?? string.Empty;
        }

        /// <summary>
        /// Type of the deployment
        /// </summary>
        [JsonPropertyName("object")]
        [SuppressMessage("Globalization", "CA1308:Normalize strings to uppercase", Justification = "Azure API expects lowercase")]
        public string Type
        {
            get => this._type;
            // ReSharper disable once ConditionalAccessQualifierIsNonNullableAccordingToAPIContract
            set => this._type = value?.ToLowerInvariant().Trim() ?? string.Empty;
        }

        /// <summary>
        /// Returns true if the deployment is active.
        /// </summary>
        /// <returns>Returns true if the deployment is active.</returns>
        public bool IsAvailableDeployment()
        {
            return this.Type == "deployment" && this.Status == "succeeded";
        }
    }

    /// <summary>
    /// List of Azure OpenAI deployments
    /// </summary>
    [JsonPropertyName("data")]
    public IList<AzureDeployment> Deployments { get; set; } = new List<AzureDeployment>();
}
