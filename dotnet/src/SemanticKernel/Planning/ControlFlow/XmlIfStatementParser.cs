// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Xml;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

internal class XmlIfStatementParser : IStatementParser<IfStatement>
{
    // Parses an XML string into an IfStatement instance
    public IfStatement Parse(string ifXml)
    {
        // Create an XML document from the string
        var doc = new XmlDocument();
        doc.LoadXml(ifXml);

        // Get the root element
        var ifElement = doc.DocumentElement;
        if (!string.Equals(ifElement.Name, "if", StringComparison.OrdinalIgnoreCase))
        {
            throw new NotSupportedException($"Element {ifElement.Name} is not supported as a statement");
        }

        // Get the conditiongroup element
        var conditionGroupElement = ifElement.SelectSingleNode("conditiongroup") as XmlElement;
        if (conditionGroupElement is null )
        {
            throw new NotSupportedException("If statement must have a conditiongroup element");
        }

        // Get the then and else elements
        var thenElement = ifElement.SelectSingleNode("then") as XmlElement;
        if (thenElement is null)
        {
            throw new NotSupportedException("If statement must have a then element");
        }

        var elseElement = ifElement.SelectSingleNode("else") as XmlElement;

        // Get the inner XML of the then and else elements
        var thenXml = thenElement?.InnerXml;
        var elseXml = elseElement?.InnerXml;

        // Create a ConditionGroup instance from the conditiongroup element
        var conditionGroup = ParseConditionGroup(conditionGroupElement);

        // Create an IfStatement instance from the ConditionGroup and the then and else XML
        var ifStatement = new IfStatement(conditionGroup, thenXml, elseXml);

        return ifStatement;
    }

    // Parses an XML element into a ConditionGroup instance
    private static ConditionGroup ParseConditionGroup(XmlElement conditionGroupElement)
    {
        // Create a ConditionGroup instance
        var conditionGroup = new ConditionGroup();

        // Get the check and conditiongroup child elements
        var checkElements = conditionGroupElement.SelectNodes("condition");
        var conditionGroupElements = conditionGroupElement.SelectNodes("conditiongroup");

        // Loop through the check elements and create Check instances
        foreach (XmlElement conditionElement in checkElements)
        {
            // Get the type attribute
            var type = conditionElement.GetAttribute("type");

            // Create a Check instance based on the type
            var check = CreateCondition(type, conditionElement);

            // Add the Check instance to the Checks collection
            conditionGroup.Conditions.Add(check);
        }

        // Loop through the conditiongroup elements and create ConditionGroup instances
        foreach (XmlElement nestedConditionGroupElement in conditionGroupElements)
        {
            // Recursively parse the conditiongroup element
            var nestedConditionGroup = ParseConditionGroup(nestedConditionGroupElement);

            // Add the ConditionGroup instance to the ConditionGroups collection
            conditionGroup.ConditionGroups.Add(nestedConditionGroup);
        }

        return conditionGroup;
    }

    // Creates a Check instance based on the type and the XML element
    private static Condition CreateCondition(string type, XmlElement conditionElement)
    {
        // Use a switch statement or a factory method to create the appropriate Condition class
        switch (type)
        {
            case "Exact":
                // Get the variable and exact attributes
                var variableName = conditionElement.GetAttribute("variable");
                var exactValue = conditionElement.GetAttribute("exact");

                // Create a CheckExact instance
                var exactCondition = new ExactCondition(variableName, exactValue);

                return exactCondition;

            // Add more cases for other types of checks

            default:
                // Throw an exception if the type is not recognized
                throw new ArgumentException($"Invalid condition type: {type}");
        }
    }
}
