// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

/// <summary>
/// Represents a yaml configuration file for an assistant.
/// </summary>
internal sealed class AssistantConfigurationModel
{
    /// <summary>
    /// The assistant name
    /// </summary>
    [YamlMember(Alias = "name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The assistant description
    /// </summary>
    [YamlMember(Alias = "description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// The assistant instructions template
    /// </summary>
    [YamlMember(Alias = "instructions")]
    public string Instructions { get; set; } = string.Empty;

    ///// <summary>
    ///// The assistant instructions template
    ///// </summary>
    //[YamlMember(Alias = "template")]
    //public string Template { get; set; } = string.Empty;

    ///// <summary>
    ///// The assistant instruction template format.
    ///// </summary>
    //[YamlMember(Alias = "template_format")]
    //public string TemplateFormat { get; set; } = string.Empty;

    ///// <summary>
    ///// Describes the input variables for the template.
    ///// </summary>
    //[YamlMember(Alias = "input_variables")]
    //public List<VariableViewModel> InputVariables { get; set; }

    ///// <summary>
    ///// Describes known valid models.
    ///// </summary>
    //[YamlMember(Alias = "execution_settings")]
    //public List<ExecutionSettingsModel> ExecutionSettings { get; set; }
}
