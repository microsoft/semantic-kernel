// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.orchestration.WritableContextVariables;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

/** Parse sequential plan text into a plan. */
public class SequentialPlanParser {
    private static final Logger LOGGER = LoggerFactory.getLogger(SequentialPlanParser.class);

    // The tag name used in the plan xml for the user's goal/ask.
    private static final String GoalTag = "goal";

    // The tag name used in the plan xml for the solution.
    private static final String SolutionTag = "plan";

    // The tag name used in the plan xml for a step that calls a skill function.
    private static final String FunctionTag = "function.";

    // The attribute tag used in the plan xml for setting the context variable name to set the
    // output of a function to.
    private static final String SetContextVariableTag =
            "setContextVariable".toLowerCase(Locale.ROOT);

    // The attribute tag used in the plan xml for appending the output of a function to the final
    // result for a plan.
    private static final String AppendToResultTag = "appendToResult".toLowerCase(Locale.ROOT);

    /**
     * Convert a plan xml string to a plan
     *
     * @param xmlString The plan xml string
     * @param goal The goal for the plan
     * @param skills The skills to use
     * @return The plan
     * @throws PlanningException
     */
    public static Plan toPlanFromXml(String xmlString, String goal, ReadOnlySkillCollection skills)
            throws PlanningException {

        try {
            DocumentBuilder db = DocumentBuilderFactory.newInstance().newDocumentBuilder();

            Document doc =
                    db.parse(
                            new ByteArrayInputStream(
                                    ("<xml>" + xmlString + "</xml>")
                                            .getBytes(StandardCharsets.UTF_8)));

            NodeList solution = doc.getElementsByTagName(SolutionTag);

            Plan plan = new Plan(goal, () -> skills);

            for (int i = 0; i < solution.getLength(); i++) {
                Node solutionNode = solution.item(i);
                String parentNodeName = solutionNode.getNodeName();

                for (int j = 0; j < solutionNode.getChildNodes().getLength(); j++) {
                    Node childNode = solutionNode.getChildNodes().item(j);
                    if (childNode.getNodeName().equals("#text")) {
                        if (childNode.getNodeValue() != null
                                && !childNode.getNodeValue().trim().isEmpty()) {
                            plan.addSteps(new Plan(childNode.getNodeValue().trim(), () -> skills));
                        }
                        continue;
                    }

                    if (childNode.getNodeName().toLowerCase(Locale.ROOT).startsWith(FunctionTag)) {
                        String[] skillFunctionNameParts =
                                childNode.getNodeName().split(FunctionTag, -1);
                        String skillFunctionName = "";

                        if (skillFunctionNameParts.length > 1) {
                            skillFunctionName = skillFunctionNameParts[1];
                        }

                        String skillName = getSkillName(skillFunctionName);
                        String functionName = getFunctionName(skillFunctionName);

                        if (functionName != null
                                && !functionName.isEmpty()
                                && skills.hasFunction(skillName, functionName)) {
                            SKFunction skillFunction =
                                    Objects.requireNonNull(skills.getFunctions(skillName))
                                            .getFunction(functionName, SKFunction.class);

                            WritableContextVariables functionVariables =
                                    getFunctionVariables(skillFunction, childNode);
                            List<String> functionOutputs = getFunctionOutputs(childNode);
                            List<String> functionResults = getFunctionResults(childNode);

                            Plan planStep =
                                    new Plan(
                                            skillFunction,
                                            functionVariables,
                                            SKBuilders.variables().build(),
                                            functionOutputs,
                                            () -> skills);

                            plan.addOutputs(functionResults);
                            plan.addSteps(planStep);
                        } else {
                            LOGGER.trace(
                                    "{}: appending function node {}",
                                    parentNodeName,
                                    skillFunctionName);
                            plan.addSteps(new Plan(childNode.getTextContent(), () -> skills));
                        }

                        continue;
                    }

                    plan.addSteps(new Plan(childNode.getTextContent(), () -> skills));
                }
            }
            return plan;

        } catch (RuntimeException | ParserConfigurationException | IOException | SAXException e) {
            throw new PlanningException(
                    PlanningException.ErrorCodes.InvalidPlan, "Failed to parse plan xml.", e);
        }
    }

    private static WritableContextVariables getFunctionVariables(
            SKFunction skillFunction, Node node) {
        WritableContextVariables functionVariables = SKBuilders.variables().build().writableClone();

        FunctionView description = skillFunction.describe();

        if (description != null) {
            description
                    .getParameters()
                    .forEach(
                            p -> {
                                functionVariables.setVariable(p.getName(), p.getDefaultValue());
                            });
        }

        if (node.getAttributes() != null) {
            for (int k = 0; k < node.getAttributes().getLength(); k++) {
                Node attr = node.getAttributes().item(k);
                String nodeName = attr.getNodeName().toLowerCase(Locale.ROOT);
                if (!nodeName.equals(SetContextVariableTag)
                        && !nodeName.equals(AppendToResultTag)) {
                    functionVariables.setVariable(attr.getNodeName(), attr.getTextContent());
                }
            }
        }
        return functionVariables;
    }

    private static List<String> getFunctionOutputs(Node node) {
        List<String> functionOutputs = new ArrayList<>();
        for (int k = 0; k < node.getAttributes().getLength(); k++) {
            Node attr = node.getAttributes().item(k);
            String nodeName = attr.getNodeName().toLowerCase(Locale.ROOT);
            if (nodeName.equals(SetContextVariableTag) || nodeName.equals(AppendToResultTag)) {
                functionOutputs.add(attr.getTextContent());
            }
        }
        return functionOutputs;
    }

    private static List<String> getFunctionResults(Node node) {
        List<String> functionResults = new ArrayList<>();
        for (int k = 0; k < node.getAttributes().getLength(); k++) {
            Node attr = node.getAttributes().item(k);
            String nodeName = attr.getNodeName().toLowerCase(Locale.ROOT);
            if (nodeName.equals(AppendToResultTag)) {
                functionResults.add(attr.getTextContent());
            }
        }
        return functionResults;
    }

    private static String getSkillName(String skillFunctionName) {
        String[] skillFunctionNameParts = skillFunctionName.split("\\.", -1);
        return skillFunctionNameParts.length > 0 ? skillFunctionNameParts[0] : "";
    }

    private static String getFunctionName(String skillFunctionName) {
        String[] skillFunctionNameParts = skillFunctionName.split("\\.", -1);
        return skillFunctionNameParts.length > 1 ? skillFunctionNameParts[1] : skillFunctionName;
    }
}
