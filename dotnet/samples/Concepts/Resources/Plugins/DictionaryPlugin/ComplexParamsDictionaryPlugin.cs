// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace Plugins.DictionaryPlugin;

/// <summary>
/// Plugin example with two Local functions, where one function gets a random word and the other returns a definition for a given word.
/// </summary>
public sealed class ComplexParamsDictionaryPlugin
{
    public const string PluginName = nameof(ComplexParamsDictionaryPlugin);

    private readonly List<DictionaryEntry> _dictionary =
        [
            new DictionaryEntry("apple", "a round fruit with red, green, or yellow skin and a white flesh"),
            new DictionaryEntry("book", "a set of printed or written pages bound together along one edge"),
            new DictionaryEntry("cat", "a small furry animal with whiskers and a long tail that is often kept as a pet"),
            new DictionaryEntry("dog", "a domesticated animal with four legs, a tail, and a keen sense of smell that is often used for hunting or companionship"),
            new DictionaryEntry("elephant", "a large gray mammal with a long trunk, tusks, and ears that lives in Africa and Asia")
        ];

    [KernelFunction, Description("Gets a random word from a dictionary of common words and their definitions.")]
    public DictionaryEntry GetRandomEntry()
    {
        // Get random number
        var index = RandomNumberGenerator.GetInt32(0, this._dictionary.Count - 1);

        // Return the word at the random index
        return this._dictionary[index];
    }

    [KernelFunction, Description("Gets the word for a given dictionary entry.")]
    public string GetWord([Description("Word to get definition for.")] DictionaryEntry entry)
    {
        // Return the definition or a default message
        return this._dictionary.FirstOrDefault(e => e.Word == entry.Word)?.Word ?? "Entry not found";
    }

    [KernelFunction, Description("Gets the definition for a given word.")]
    public string GetDefinition([Description("Word to get definition for.")] string word)
    {
        // Return the definition or a default message
        return this._dictionary.FirstOrDefault(e => e.Word == word)?.Definition ?? "Word not found";
    }
}

/// <summary>
/// In order to use custom types, <see cref="TypeConverter"/> should be specified,
/// that will convert object instance to string representation.
/// </summary>
/// <remarks>
/// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
/// it can be passed to AI for further processing using prompt functions.
/// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
/// </remarks>
[TypeConverter(typeof(DictionaryEntryConverter))]
public sealed class DictionaryEntry
{
    public string Word { get; set; } = string.Empty;
    public string Definition { get; set; } = string.Empty;

    public DictionaryEntry(string word, string definition)
    {
        this.Word = word;
        this.Definition = definition;
    }
}

/// <summary>
/// Implementation of <see cref="TypeConverter"/> for <see cref="DictionaryEntry"/>.
/// In this example, object instance is serialized with <see cref="JsonSerializer"/> from System.Text.Json,
/// but it's possible to convert object to string using any other serialization logic.
/// </summary>
public sealed class DictionaryEntryConverter : TypeConverter
{
    public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

    /// <summary>
    /// This method is used to convert object from string to actual type. This will allow to pass object to
    /// Local function which requires it.
    /// </summary>
    public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
    {
        return JsonSerializer.Deserialize<DictionaryEntry>((string)value);
    }

    /// <summary>
    /// This method is used to convert actual type to string representation, so it can be passed to AI
    /// for further processing.
    /// </summary>
    public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
    {
        return JsonSerializer.Serialize(value);
    }
}
