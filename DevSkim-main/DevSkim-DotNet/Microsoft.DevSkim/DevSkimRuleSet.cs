// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Microsoft.ApplicationInspector.RulesEngine;

namespace Microsoft.DevSkim
{
    /// <summary>
    ///     Storage for rules
    /// </summary>
    public class DevSkimRuleSet : TypedRuleSet<DevSkimRule>
    {
        /// <summary>
        ///     Creates instance of Ruleset
        /// </summary>
        public DevSkimRuleSet()
        {
        }

        /// <summary>
        /// Load the default rules embedded in the DevSkim binary
        /// </summary>
        /// <returns>A <see cref="DevSkimRuleSet"/> </returns>
        public static DevSkimRuleSet GetDefaultRuleSet()
        {
            DevSkimRuleSet ruleSet = new DevSkimRuleSet();
            Assembly assembly = ruleSet.GetType().Assembly;
            string[] resNames = Assembly.GetExecutingAssembly().GetManifestResourceNames();
            foreach (string resName in resNames.Where(x => x.StartsWith("Microsoft.DevSkim.rules.default") && x.EndsWith(".json")))
            {
                Stream? resource = assembly.GetManifestResourceStream(resName);
                using StreamReader file = new StreamReader(resource ?? new MemoryStream());
                string value = file.ReadToEnd();
                ruleSet.AddString(value, resName, null);
            }

            return ruleSet;
        }

        /// <summary>
        /// Returns a new <see cref="DevSkimRuleSet"/> with only rules that have an ID matching one of the ids provided in <paramref name="ruleIds"/>
        /// </summary>
        /// <param name="ruleIds"></param>
        /// <returns></returns>
        public DevSkimRuleSet WithIds(IEnumerable<string> ruleIds)
        {
            DevSkimRuleSet newSet = new DevSkimRuleSet();
            newSet.AddRange(this.Where(x => ruleIds.Contains(x.Id)));
            return newSet;
        }

        /// <summary>
        /// Returns a new <see cref="DevSkimRuleSet"/> with no rules that have an ID matching one of the ids provided in <paramref name="optsIgnoreRuleIds"/>
        /// </summary>
        /// <param name="optsIgnoreRuleIds"></param>
        /// <returns></returns>
        /// <exception cref="NotImplementedException"></exception>
        public DevSkimRuleSet WithoutIds(IEnumerable<string> optsIgnoreRuleIds)
        {
            DevSkimRuleSet newSet = new DevSkimRuleSet();
            newSet.AddRange(this.Where(x => !optsIgnoreRuleIds.Contains(x.Id)));
            return newSet;
        }
    }
}
