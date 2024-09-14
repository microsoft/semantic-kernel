using System.Collections.Generic;
using System.Linq;
using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    public class DevSkimRulesVerificationResult
    {
        private readonly RulesVerifierResult _aiResult;
        public DevSkimRulesVerificationResult(RulesVerifierResult aiResult)
        {
            _aiResult = aiResult;
        }

        public IEnumerable<RuleStatus> Errors => DevSkimRuleStatuses.Where(x => x.Errors.Any());
        public List<RuleStatus> DevSkimRuleStatuses { get; } = new List<RuleStatus>();
        public AbstractRuleSet CompiledRuleSet => _aiResult.CompiledRuleSet;

        public bool Verified => _aiResult.RuleStatuses.All(x => x.Verified) &&
                                DevSkimRuleStatuses.All(x => x.Verified);
    }
}