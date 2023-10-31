# Semantic Kernel for Java Packages

The semantic kernel has the packages below, all are under the groupId `com.microsoft.semantic-kernel`, and can be imported
to maven.

```xml
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-api</artifactId>
    </dependency>
```

A BOM is provided that can be used to define the versions of all semantic kernel packages.

```xml
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.microsoft.semantic-kernel</groupId>
                <artifactId>semantickernel-bom</artifactId>
                <version>${semantickernel.version}</version>
                <scope>import</scope>
                <type>pom</type>
            </dependency>
        </dependencies>
    </dependencyManagement>
```

## Common Packages

`semantickernel-bom`
: A Maven project BOM that can be used to define the versions of all semantic kernel packages.

`semantickernel-api`
: Main API for the semantic kernel. Defines the core public API for the semantic kernel.

`semantickernel-core`
: An implementation of the semantic kernel API. This package contains the core implementation of the semantic kernel. This
should be made available to the application at runtime, however these classes are considered internal and should not be used directly
by the application as they may change without notice.

## Connectors

`semantickernel-connectors-ai-openai`
: Provides a connector that can be used to interact with an OpenAI API.

### Memory Connectors

#### JDBC Memory Connectors

Provides a memory connector that can be used to interact with a JDBC database.
- `semantickernel-connectors-memory-sqlite`
- `semantickernel-connectors-memory-postgresql`
- `semantickernel-connectors-memory-mysql`

`semantickernel-connectors-memory-azurecognitivesearch`
: Provides a memory connector that allows using Azure Cognitive Search as a memory.

### Miscellaneous Packages

`semantickernel-planners`
: Implementations of various planners that can be used to plan the execution of semantic functions.

`semantickernel-plugin-core`
: Several example plugins, many of which are used in the samples.

`semantickernel-gpt3-tokenizer`
: A tokenizer that can be used to tokenize text for use with GPT-3. Can be used to estimate cost.


# Example configurations

### A simple project that uses Open AI for text/chat completion with a SQLite database as memory

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.microsoft.semantic-kernel</groupId>
            <artifactId>semantickernel-bom</artifactId>
            <version>${semantickernel.version}</version>
            <scope>import</scope>
            <type>pom</type>
        </dependency>
    </dependencies>
</dependencyManagement>
<dependencies>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-api</artifactId>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-core</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-connectors-ai-openai</artifactId>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-connectors-memory-sqlite</artifactId>
    </dependency>
</dependencies>
```

### A project that uses Open AI for planning with a Azure Cognitive Search as memory

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.microsoft.semantic-kernel</groupId>
            <artifactId>semantickernel-bom</artifactId>
            <version>${semantickernel.version}</version>
            <scope>import</scope>
            <type>pom</type>
        </dependency>
    </dependencies>
</dependencyManagement>
<dependencies>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-api</artifactId>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-core</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-connectors-ai-openai</artifactId>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-connectors-memory-azurecognitivesearch</artifactId>
    </dependency>
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-planners</artifactId>
    </dependency>
</dependencies>
```


