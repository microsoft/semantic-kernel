using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    public class DevSkimRuleVerifierOptions : RulesVerifierOptions
    {
        public DevSkimRuleVerifierOptions()
        {
            DisableRequireUniqueIds = true;
        }
    }
}