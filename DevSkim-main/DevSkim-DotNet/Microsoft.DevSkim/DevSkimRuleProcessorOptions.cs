using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    public class DevSkimRuleProcessorOptions : RuleProcessorOptions
    {
        public DevSkimRuleProcessorOptions()
        {
            AllowAllTagsInBuildFiles = true;
            Languages = DevSkimLanguages.LoadEmbedded();
        }

        public bool EnableSuppressions { get; set; } = true;
    }
}
