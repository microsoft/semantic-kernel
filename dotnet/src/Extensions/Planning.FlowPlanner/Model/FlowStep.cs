// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

public class FlowStep
{
    private List<string> _requires = new();

    private List<string> _provides = new();

    private Dictionary<string, Type?> _skillTypes = new();

    private Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? _skillsFactory;

    public FlowStep(string goal, Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? skillsFactory = null)
    {
        this.Goal = goal;
        this._skillsFactory = skillsFactory;
    }

    /// <summary>
    /// Deserialization only
    /// </summary>
    public FlowStep() : this(string.Empty)
    {
    }

    public string Goal { get; set; }

    public List<string> Requires
    {
        get => this._requires;
        set => this._requires = value;
    }

    public List<string> Provides
    {
        get => this._provides;
        set => this._provides = value;
    }

    public List<string>? Skills
    {
        get => this._skillTypes.Keys.ToList();
        set
        {
            Dictionary<string, Type?> skills = new();

            if (value != null)
            {
                var types = AppDomain.CurrentDomain.GetAssemblies()
                    .Where(a => !a.IsDynamic)
                    .SelectMany(a => a.GetTypes())
                    .ToList();

                foreach (var skillName in value)
                {
                    if (skillName == null)
                    {
                        continue;
                    }

                    var type = types.FirstOrDefault(predicate: t => t.FullName?.Equals(skillName, StringComparison.OrdinalIgnoreCase) ?? false);
                    if (type == null)
                    {
                        type = types.FirstOrDefault(t => t.FullName?.Contains(skillName) ?? false);

                        if (type == null)
                        {
                            // If not found, assume the skill would be loaded separately.
                            skills.Add(skillName, null);
                            continue;
                        }
                    }

                    skills.Add(skillName, type);
                }
            }

            this._skillTypes = skills;
            this._skillsFactory = (kernel, globalSkills) =>
            {
                return this._skillTypes.Select(kvp =>
                {
                    var skillName = kvp.Key;
                    var type = kvp.Value;
                    if (type != null)
                    {
                        try
                        {
                            return Activator.CreateInstance(type, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new object[] { kernel }, null);
                        }
                        catch (MissingMethodException)
                        {
                            try
                            {
                                return Activator.CreateInstance(type, true);
                            }
                            catch (MissingMethodException)
                            {
                            }
                        }
                    }

                    return globalSkills.FirstOrDefault(_ => _.Key.GetType().Name.Contains(skillName)).Key;
                }).Where(skill => skill != null).ToList();
            };
        }
    }

    public void AddRequires(params string[] requiredArguments)
    {
        this.ValidateArguments(requiredArguments);
        this._requires.AddRange(requiredArguments);
    }

    public void AddProvides(params string[] providedArguments)
    {
        this.ValidateArguments(providedArguments);
        this._provides.AddRange(providedArguments);
    }

    public IEnumerable<object> GetSKills(IKernel kernel, Dictionary<object, string?> globalSkills)
    {
        if (this._skillsFactory != null)
        {
            return this._skillsFactory(kernel, globalSkills);
        }

        return Enumerable.Empty<object>();
    }

    public bool DependsOn(FlowStep otherStep)
    {
        return this.Requires.Intersect(otherStep.Provides).Any();
    }

    private void ValidateArguments(string[] arguments)
    {
        var invalidArguments = arguments.Intersect(Constants.ActionVariableNames.All).ToArray();

        if (invalidArguments.Length != 0)
        {
            throw new ArgumentException($"Invalid arguments: {string.Join(",", invalidArguments)}");
        }
    }
}
