using System.Text.RegularExpressions;
using System.Xml.Linq;
using Prompty.Core.Types;
using Scriban;

namespace Prompty.Core.Renderers;

public class RenderPromptLiquidTemplate
{
    private string _templatesGeneraged;
    private Prompty _prompty;

    // create private invokerfactory and init it

    public RenderPromptLiquidTemplate(Prompty prompty)
    {
        _prompty = prompty;
    }
    

    public void RenderTemplate()
    {
        var template = Template.ParseLiquid(_prompty.Prompt);
        _prompty.Prompt = template.Render(_prompty.Inputs);
        _templatesGeneraged = _prompty.Prompt;
        
    }

}
