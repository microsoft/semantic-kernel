# Valid prompt syntax scenarios

## Chat history placeholders helper

### Variables

```csharp
ChatHistory chatHistory = [];
chatHistory.AddUserMessage("Hello, my name is Matthew!");
chatHistory.AddAssistantMessage("Nice to meet you Matthew!");
chatHistory.AddUserMessage("I'm looking for a new car.");

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "chatHistory", chatHistory }, // Unsafe by default
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
{{placeholder $chatHistory}}
```

**Handlebars Template Language**

```handlebars
{{placeholder chatHistory}}
```

### Rendered intermediate template

```xml
<message role="user">
    Hello, my name is Matthew!
</message>
<message role="assistant">
    Nice to meet you Matthew!
</message>
<message role="user">
    I'm looking for a new car.
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "user",
            "content": "Hello, my name is Matthew!"
        },
        {
            "role": "assistant",
            "content": "Nice to meet you Matthew!"
        },
        {
            "role": "user",
            "content": "I'm looking for a new car."
        }
    ]
}
```

## Raw chat history string variable

### Variables

```csharp
string chatHistory = @"
    <message role=""user"">
        Hello, my name is Matthew!
    </message>
    <message role=""assistant"">
        Nice to meet you Matthew!
    </message>
    <message role=""user"">
        I'm looking for a new car.
    </message>";

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "chatHistory", chatHistory, true }, // Safe
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
{{$chatHistory}}
```

**Handlebars Template Language**

```handlebars
{{chatHistory}}
```

### Rendered intermediate template

```xml
<message role="user">
    Hello, my name is Matthew!
</message>
<message role="assistant">
    Nice to meet you Matthew!
</message>
<message role="user">
    I'm looking for a new car.
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "user",
            "content": "Hello, my name is Matthew!"
        },
        {
            "role": "assistant",
            "content": "Nice to meet you Matthew!"
        },
        {
            "role": "user",
            "content": "I'm looking for a new car."
        }
    ]
}
```


## Asking the AI about XML encoding and decoding

### Variables

```csharp
string input = @"
    What is wrong with this React code?

    ```html
    <div>
        <message role=""user"">Hello!</message>
        <message role=""assistant"">How are you?</message>
    </div>
    ```
    ";

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "input", input }, // Unsafe
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
<message role="user">{{$input}}</message>
```

**Handlebars Template Language**

```handlebars
<message role="user">{{input}}</message>
```

### Rendered intermediate template

```xml
<message role="user">
    What is wrong with this React code?

    ```html
    &#60;div&#62;
        &#60;message role="user"&#62;Hello!&#60;/message&#62;
        &#60;message role="assistant"&#62;How are you?&#60;/message&#62;
    &#60;/div&#62;
    ```
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "user",
            "content": "What is wrong with this React code?\n\n```html\n<div>\n    <message role=\"user\">Hello!</message>\n    <message role=\"assistant\">How are you?</message>\n</div>\n```"
        }
    ]
}
```

## Asking the AI about XML encoding and decoding

### Variables

```csharp
string input = @"
    Is the encoding of < equal to &lt; in XML?
    ";

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "input", input }, // Unsafe
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
<message role="user">{{$input}}</message>
```

**Handlebars Template Language**

```handlebars
<message role="user">{{input}}</message>
```

### Rendered intermediate template

```xml
<message role="user">
   Is the encoding of &#60; equal to &#38;lt; in XML?
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "user",
            "content": "Is the encoding of < equal to &lt; in XML?"
        }
    ]
}
```

## Including item collection items

### Variables

```csharp
string image = "<image src=\"https://example.com/image.png\" />";
string text = @"What's in the image?";

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "text", text }, // Safe
        { "image", image, true }, // Safe
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
<message role="user">
    {{$image}}
    {{$text}}
</message>
```

**Handlebars Template Language**

```handlebars
<message role="user">
    {{image}}
    {{text}}
</message>
```

### Rendered intermediate template

```xml
<message role="user">
    <image src="https://example.com/image.png" />
    What's in the image?
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "src": "https://example.com/image.png"
                },
                {
                    "type": "text",
                    "content": "What's in the image?"
                }
            ]
        }
    ]
}
```

## Using CDATA to avoid needing to encode in template

### Variables

```csharp
string input = @"
    Write a sample with the available React components
    ";

var results = await kernel.InvokeAsync(
    template, // See below
    new ()
    {
        { "input", input }, // Unsafe
    }
)
```

### Prompts template

**Semantic Kernel Template Language**

```xml
<message role="system">
    These are the availble React components:
    <![CDATA[
        <message>Hello!</message>
        <image src="https://example.com/image.png" />
        <video src="https://example.com/video.mp4" />
        <audio src="https://example.com/audio.mp3" />
    ]]>
</message>
<message role="user">{{$input}}</message>
```

**Handlebars Template Language**

```handlebars
<message role="system">
    These are the availble React components:
    <![CDATA[
        <message>Hello!</message>
        <image src="https://example.com/image.png" />
        <video src="https://example.com/video.mp4" />
        <audio src="https://example.com/audio.mp3" />
    ]]>
</message>
<message role="user">{{input}}</message>
```

### Rendered intermediate template

```xml
<message role="system">
    These are the availble React components:
    <![CDATA[
        <message>Hello!</message>
        <image src="https://example.com/image.png" />
        <video src="https://example.com/video.mp4" />
        <audio src="https://example.com/audio.mp3" />
    ]]>
</message>
<message role="user">
    Write a sample with the available React components
</message>
```

### Final chat history object

```json
{
    "messages": [
        {
            "role": "system",
            "content": "These are the availble React components:\n        <message>Hello!</message>\n        <image src=\"https://example.com/image.png\" />\n        <video src=\"https://example.com/video.mp4\" />\n        <audio src=\"https://example.com/audio.mp3\" />"
        },
        {
            "role": "user",
            "content": "Write a sample with the available React components"
        }
    ]
}
```

