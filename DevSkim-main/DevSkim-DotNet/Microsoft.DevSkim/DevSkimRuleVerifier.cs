using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    public class DevSkimRuleVerifier
    {
        private RulesVerifier _appInspectorVerifier;
        public DevSkimRuleVerifier(DevSkimRuleVerifierOptions options)
        {
            _appInspectorVerifier = new RulesVerifier(options);
        }

        public DevSkimRulesVerificationResult Verify(DevSkimRuleSet ruleSet)
        {
            RulesVerifierResult aiResult = _appInspectorVerifier.Verify(ruleSet);
            DevSkimRulesVerificationResult devSkimResult = new DevSkimRulesVerificationResult(aiResult);
            foreach (RuleStatus status in aiResult.RuleStatuses)
            {
                devSkimResult.DevSkimRuleStatuses.Add(status);
            }
            // TODO: Validate devskim specific stuff like fix-its
            return devSkimResult;
        }
    }
}