// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Skills.Core;

internal static class SemanticFunctionConstants
{
    internal const string SummarizeConversationDefinition =
        @"BEGIN CONTENT TO SUMMARIZE:
{{$INPUT}}

END CONTENT TO SUMMARIZE.

Summarize the conversation in 'CONTENT TO SUMMARIZE', identifying main points of discussion and any conclusions that were reached.
Do not incorporate other general knowledge.
Summary is in plain text, in complete sentences, with no markup or tags.

BEGIN SUMMARY:
";

    internal const string GetConversationActionItemsDefinition =
        @"You are an action item extractor. You will be given chat history and need to make note of action items mentioned in the chat.
Extract action items from the content if there are any. If there are no action, return nothing. If a single field is missing, use an empty string.
Return the action items in json.

Possible statuses for action items are: Open, Closed, In Progress.

EXAMPLE INPUT WITH ACTION ITEMS:

John Doe said: ""I will record a demo for the new feature by Friday""
I said: ""Great, thanks John. We may not use all of it but it's good to get it out there.""

EXAMPLE OUTPUT:
{
    ""actionItems"": [
        {
            ""owner"": ""John Doe"",
            ""actionItem"": ""Record a demo for the new feature"",
            ""dueDate"": ""Friday"",
            ""status"": ""Open"",
            ""notes"": """"
        }
    ]
}

EXAMPLE INPUT WITHOUT ACTION ITEMS:

John Doe said: ""Hey I'm going to the store, do you need anything?""
I said: ""No thanks, I'm good.""

EXAMPLE OUTPUT:
{
    ""action_items"": []
}

CONTENT STARTS HERE.

{{$INPUT}}

CONTENT STOPS HERE.

OUTPUT:";

    internal const string GetConversationTopicsDefinition =
        @"Analyze the following extract taken from a conversation transcript and extract key topics.
- Topics only worth remembering.
- Be brief. Short phrases.
- Can use broken English.
- Conciseness is very important.
- Topics can include names of memories you want to recall.
- NO LONG SENTENCES. SHORT PHRASES.
- Return in JSON
[Input]
My name is Macbeth. I used to be King of Scotland, but I died. My wife's name is Lady Macbeth and we were married for 15 years. We had no children. Our beloved dog Toby McDuff was a famous hunter of rats in the forest.
My tragic story was immortalized by Shakespeare in a play.
[Output]
{
  ""topics"": [
    ""Macbeth"",
    ""King of Scotland"",
    ""Lady Macbeth"",
    ""Dog"",
    ""Toby McDuff"",
    ""Shakespeare"",
    ""Play"",
    ""Tragedy""
  ]
}
+++++
[Input]
{{$INPUT}}
[Output]";
}
