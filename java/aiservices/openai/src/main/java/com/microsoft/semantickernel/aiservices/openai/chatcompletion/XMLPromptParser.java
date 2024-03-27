// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestUserMessage;
import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import javax.xml.namespace.QName;
import javax.xml.stream.XMLEventReader;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.events.Attribute;
import javax.xml.stream.events.StartElement;
import javax.xml.stream.events.XMLEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class XMLPromptParser {

    private static final Logger LOGGER = LoggerFactory.getLogger(XMLPromptParser.class);

    public static ParsedPrompt parse(String rawPrompt) {
        List<String> prompts = Arrays.asList(
            rawPrompt,
            "<prompt>" + rawPrompt + "</prompt>");

        for (String prompt : prompts) {
            try {
                List<ChatRequestMessage> parsedMessages = getChatRequestMessages(prompt);
                List<FunctionDefinition> parsedFunctions = getFunctionDefinitions(prompt);

                if (!parsedMessages.isEmpty()) {
                    return new ParsedPrompt(parsedMessages, parsedFunctions);
                }
            } catch (SKException e) {
                //ignore
            }
        }

        ChatRequestUserMessage message = new ChatRequestUserMessage(rawPrompt);

        if (message.getName() == null) {
            message.setName(UUID.randomUUID().toString());
        }

        return new ParsedPrompt(Collections.singletonList(message), null);
    }

    private static List<ChatRequestMessage> getChatRequestMessages(String prompt) {

        // TODO: XML parsing should be done as a chain of XMLEvent handlers.
        // If one handler does not recognize the element, it should pass it to the next handler.
        // In this way, we can avoid parsing the whole prompt twice and easily extend the parsing logic.
        List<ChatRequestMessage> messages = new ArrayList<>();
        try (InputStream is = new ByteArrayInputStream(prompt.getBytes(StandardCharsets.UTF_8))) {
            XMLInputFactory factory = XMLInputFactory.newInstance();
            XMLEventReader reader = factory.createXMLEventReader(is);
            while (reader.hasNext()) {
                XMLEvent event = reader.nextEvent();
                if (event.isStartElement()) {
                    String name = getElementName(event);
                    if (name.equals("message")) {
                        String role = getAttributeValue(event, "role");
                        String content = reader.getElementText();
                        messages.add(getChatRequestMessage(role, content));
                    }
                }
            }
        } catch (IOException | XMLStreamException | IllegalArgumentException e) {
            throw new SKException("Failed to parse messages");
        }
        return messages;
    }

    private static List<FunctionDefinition> getFunctionDefinitions(String prompt) {
        // TODO: XML parsing should be done as a chain of XMLEvent handlers. See previous remark.
        // <function pluginName=\"%s\" name=\"%s\"  description=\"%s\">
        //      <parameter name=\"%s\" description=\"%s\" defaultValue=\"%s\" isRequired=\"%s\" type=\"%s\"/>...
        // </function>
        List<FunctionDefinition> functionDefinitions = new ArrayList<>();
        try (InputStream is = new ByteArrayInputStream(prompt.getBytes(StandardCharsets.UTF_8))) {
            XMLInputFactory factory = XMLInputFactory.newFactory();
            XMLEventReader reader = factory.createXMLEventReader(is);
            FunctionDefinition functionDefinition = null;
            Map<String, String> parameters = new HashMap<>();
            List<String> requiredParmeters = new ArrayList<>();
            while (reader.hasNext()) {
                XMLEvent event = reader.nextEvent();
                if (event.isStartElement()) {
                    String elementName = getElementName(event);
                    if (elementName.equals("function")) {
                        assert functionDefinition == null;
                        assert parameters.isEmpty();
                        assert requiredParmeters.isEmpty();
                        String pluginName = getAttributeValue(event, "pluginName");
                        String name = getAttributeValue(event, "name");
                        String description = getAttributeValue(event, "description");
                        // name has to match '^[a-zA-Z0-9_-]{1,64}$'
                        functionDefinition = new FunctionDefinition(
                            ToolCallBehavior.formFullFunctionName(pluginName, name))
                            .setDescription(description);
                    } else if (elementName.equals("parameter")) {
                        String name = getAttributeValue(event, "name");
                        String type = getAttributeValue(event, "type").toLowerCase(Locale.ROOT);
                        String description = getAttributeValue(event, "description");
                        parameters.put(name,
                            String.format("{\"type\": \"%s\", \"description\": \"%s\"}",
                                "string",
                                description));

                        String isRequired = getAttributeValue(event, "isRequired");
                        if (Boolean.parseBoolean(isRequired)) {
                            requiredParmeters.add(name);
                        }
                    }
                } else if (event.isEndElement()) {
                    String elementName = getElementName(event);
                    if (elementName.equals("function")) {
                        // Example JSON Schema:
                        // {
                        //    "type": "function",
                        //    "function": {
                        //        "name": "get_current_weather",
                        //        "description": "Get the current weather in a given location",
                        //        "parameters": {
                        //            "type": "object",
                        //            "properties": {
                        //                "location": {
                        //                    "type": "string",
                        //                    "description": "The city and state, e.g. San Francisco, CA",
                        //                },
                        //               "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        //            },
                        //            "required": ["location"],
                        //        },
                        //    },
                        //}
                        if (functionDefinition == null) {
                            throw new SKException("Failed to parse function definition");
                        }
                        if (!parameters.isEmpty()) {
                            StringBuilder sb = new StringBuilder(
                                "{\"type\": \"object\", \"properties\": {");
                            parameters.forEach((name, value) -> {
                                // make "param": {"type": "string", "description": "desc"},
                                sb.append(String.format("\"%s\": %s,", name, value));
                            });
                            // strip off trailing comma and close the properties object
                            sb.replace(sb.length() - 1, sb.length(), "}");
                            if (!requiredParmeters.isEmpty()) {
                                sb.append(", \"required\": [");
                                requiredParmeters.forEach(name -> {
                                    sb.append(String.format("\"%s\",", name));
                                });
                                // strip off trailing comma and close the required array
                                sb.replace(sb.length() - 1, sb.length(), "]");
                            }
                            // close the object
                            sb.append("}");
                            //System.out.println(sb.toString());
                            ObjectMapper objectMapper = new ObjectMapper();
                            JsonNode jsonNode = objectMapper.readTree(sb.toString());
                            BinaryData binaryData = BinaryData.fromObject(jsonNode);
                            functionDefinition.setParameters(binaryData);
                        }
                        functionDefinitions.add(functionDefinition);
                        functionDefinition = null;
                        parameters.clear();
                        requiredParmeters.clear();
                    }
                }
            }
        } catch (IOException | XMLStreamException | IllegalArgumentException e) {
            LOGGER.error("Error parsing prompt", e);
        }
        return functionDefinitions;
    }

    private static String getElementName(XMLEvent xmlEvent) {
        if (xmlEvent.isStartElement()) {
            return xmlEvent.asStartElement().getName().getLocalPart();
        } else if (xmlEvent.isEndElement()) {
            return xmlEvent.asEndElement().getName().getLocalPart();
        }
        // TODO: programmer's error - log at debug
        return "";
    }

    private static String getAttributeValue(XMLEvent xmlEvent, String attributeName) {
        if (xmlEvent.isStartElement()) {
            StartElement element = xmlEvent.asStartElement();
            Attribute attribute = element.getAttributeByName(QName.valueOf(attributeName));
            return attribute != null ? attribute.getValue() : "";
        }
        // TODO: programmer's error - log at debug
        return "";
    }

    private static ChatRequestMessage getChatRequestMessage(
        String role,
        String content) {
        try {
            AuthorRole authorRole = AuthorRole.valueOf(role.toUpperCase(Locale.ROOT));
            return OpenAIChatCompletion.getChatRequestMessage(authorRole, content);
        } catch (IllegalArgumentException e) {
            LOGGER.debug("Unknown author role: " + role);
            throw new SKException("Unknown author role: " + role);
        }
    }
}