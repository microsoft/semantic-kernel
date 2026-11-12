# Prompt Template Engine

## Security

Semantic Kernel prompt templates are executable configuration. Function expressions such as
`{{plugin.function}}` invoke functions registered in the `Kernel` while the template is rendered, before the model
request. Use template source only from trusted sources.

Pass user-, network-, file-, or service-provided text as a template argument instead of inserting it into the template
source. Argument values are rendered as text and are not parsed as template expressions:

```python
arguments = KernelArguments(input=untrusted_text)
template = KernelPromptTemplate(
    prompt_template_config=PromptTemplateConfig(template="User input: {{$input}}")
)
rendered = await template.render(kernel, arguments)
```

Content-escaping settings, including `allow_dangerously_set_content`, do not disable function execution from template
source.

## Grammar

The Semantic Kernel uses the following grammar to parse prompt templates:

```
# BNF parsed by TemplateTokenizer
[template]       ::= "" | [block] | [block] [template]
[block]          ::= [sk-block] | [text-block]
[sk-block]       ::= "{{" [variable] "}}" | "{{" [value] "}}" | "{{" [function-call] "}}"
[text-block]     ::= [any-char] | [any-char] [text-block]
[any-char]       ::= any char

# BNF parsed by CodeTokenizer:
[template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] " " [template]
[variable]       ::= "$" [valid-name]
[value]          ::= "'" [text] "'" | '"' [text] '"'
[function-call]  ::= [function-id] | [function-id] [parameter]
[parameter]      ::= [variable] | [value]

# BNF parsed by dedicated blocks
[function-id]    ::= [valid-name] | [valid-name] "." [valid-name]
[valid-name]     ::= [valid-symbol] | [valid-symbol] [valid-name]
[valid-symbol]   ::= [letter] | [digit] | "_"
[letter]         ::= "a" | "b" ... | "z" | "A" | "B" ... | "Z"
[digit]          ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```
