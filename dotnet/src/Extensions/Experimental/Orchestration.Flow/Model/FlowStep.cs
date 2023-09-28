// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130

/// <summary>
/// Step within a <see cref="Flow"/> which defines the step goal, available skills, required and provided variables.
/// </summary>
public class FlowStep
{
    private readonly List<string> _requires = new();

    private readonly List<string> _provides = new();

    private readonly List<string> _passthrough = new();

    private Dictionary<string, Type?> _skillTypes = new();

    private Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? _skillsFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="FlowStep"/> class.
    /// </summary>
    /// <param name="goal">The goal of step</param>
    /// <param name="skillsFactory">The factory to get skills</param>
    public FlowStep(string goal, Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? skillsFactory = null)
    {
        this.Goal = goal;
        this._skillsFactory = skillsFactory;
    }

    /// <summary>
    /// Goal of the step
    /// </summary>
    public string Goal { get; set; }

    /// <summary>
    /// <see cref="CompletionType"/> of the step
    /// </summary>
    public CompletionType CompletionType { get; set; } = CompletionType.Once;

    /// <summary>
    /// If the CompletionType is CompletionType.ZeroOrMore, this message will be used to ask the user if they want to execute the current step or skip it.
    /// </summary>
    public string? StartingMessage { get; set; }

    /// <summary>
    /// If the CompletionType is CompletionType.AtLeastOnce or CompletionType.ZeroOrMore, this message will be used to ask the user if they want to try the step again.
    /// </summary>
    public string? TransitionMessage { get; set; } = "Did you want to try the previous step again?";

    /// <summary>
    /// Parameters required for executing the step
    /// </summary>
    public virtual IEnumerable<string> Requires => this._requires;

    /// <summary>
    /// Variables to be provided by the step
    /// </summary>
    public IEnumerable<string> Provides => this._provides;

    /// <summary>
    /// Variables to be passed through on iterations of the step
    /// </summary>
    public IEnumerable<string> Passthrough => this._passthrough;

    /// <summary>
    /// Gets or sets the skill available for the current step
    /// </summary>
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
                    var globalSkill = globalSkills.FirstOrDefault(_ => _.Key.GetType().Name.Contains(skillName)).Key;
                    if (globalSkill != null)
                    {
                        return globalSkill;
                    }

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

                    return null;
                }).Where(skill => skill != null).ToList()!;
            };
        }
    }

    /// <summary>
    /// Register the required arguments for the step
    /// </summary>
    /// <param name="requiredArguments">Array of required arguments</param>
    public void AddRequires(params string[] requiredArguments)
    {
        this.ValidateArguments(requiredArguments);
        this._requires.AddRange(requiredArguments);
    }

    /// <summary>
    /// Register the arguments provided by the step
    /// </summary>
    /// <param name="providedArguments">Array of provided arguments</param>
    public void AddProvides(params string[] providedArguments)
    {
        this.ValidateArguments(providedArguments);
        this._provides.AddRange(providedArguments);
    }

    /// <summary>
    /// Register the arguments passed through by the step
    /// </summary>
    /// <param name="passthroughArguments">Array of passthrough arguments</param>
    public void AddPassthrough(params string[] passthroughArguments)
    {
        if (passthroughArguments.Length != 0 && this.CompletionType != CompletionType.AtLeastOnce && this.CompletionType != CompletionType.ZeroOrMore)
        {
            throw new ArgumentException("Passthrough arguments can only be set for the AtLeastOnce or ZeroOrMore completion type");
        }

        this.ValidateArguments(passthroughArguments);
        this._passthrough.AddRange(passthroughArguments);
    }

    /// <summary>
    /// Get the skill instances registered with the step
    /// </summary>
    /// <param name="kernel">The semantic kernel</param>
    /// <param name="globalSkills">The global skills available</param>
    /// <returns></returns>
    public IEnumerable<object> GetSKills(IKernel kernel, Dictionary<object, string?> globalSkills)
    {
        if (this._skillsFactory != null)
        {
            return this._skillsFactory(kernel, globalSkills);
        }

        return Enumerable.Empty<object>();
    }

    /// <summary>
    /// Check if the step depends on another step
    /// </summary>
    /// <param name="otherStep">The other step</param>
    /// <returns>true if the step depends on the other step, false otherwise</returns>
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
