namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

public class AssistantKernelModel
{
    //[YamlMember(Alias = "name")]
    public string Name { get; set; } = string.Empty;

    /*[YamlMember(Alias = "template")]
    public string Template { get; set; }

    [YamlMember(Alias = "template_format")]
    public string TemplateFormat { get; set; }

    [YamlMember(Alias = "description")]
    public string Description { get; set; }

    [YamlMember(Alias = "input_variables")]
    public List<VariableViewModel> InputVariables { get; set; }

    [YamlMember(Alias = "execution_settings")]
    public List<ExecutionSettingsModel> ExecutionSettings { get; set; }*/
}
