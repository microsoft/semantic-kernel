using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

public class DocumentContent : KernelContent
{
    private string? _link;
    /// <summary>
    /// The Document Link.
    /// </summary>
    public string? Link
    {
        get => this._link;
        set
        {
            if (string.IsNullOrEmpty(value))
            {
                throw new ArgumentException("Link cannot be null or empty", nameof(value));
            }

            if (!value.StartsWith("http", StringComparison.OrdinalIgnoreCase))
            {
                throw new ArgumentException("Link must start with http", nameof(value));
            }

            this._link = value;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocuementContent"/> class.
    /// </summary>
    [JsonConstructor]
    public DocumentContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DocumentContent"/> class.
    /// </summary>
    /// <param name="link">Document url link.</param>
    public DocumentContent(string link) : base(link)
    {
        Verify.NotNullOrWhiteSpace(link, nameof(link));
        this.Link = link;
    }

     /// <inheritdoc/>
    public override string ToString()
    {
        return this.Link ?? string.Empty;
    }

    /// <summary>
    /// When converting a string to a <see cref="DocumentContent"/>, the content is automatically set to the string value.
    /// </summary>
    /// <param name="text">Text content</param>
    public static implicit operator DocumentContent(string text)
    {
        return new DocumentContent(text);
    }
}
