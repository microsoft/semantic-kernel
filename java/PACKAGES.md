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
: Package that defines the core public API for the semantic kernel for a Maven project.

`semantickernel-core`
: The internal implementation of the semantic kernel API.
This package contains the core implementation of the semantic kernel. This must be made available to the
application at runtime. Note that these classes are considered internal and should not be used directly by the application. Should they be used directly, it could cause instability in the application as they may change without notice over time.

## Connectors

`semantickernel-connectors-ai-openai`
: Provides a connector that can be used to interact with the OpenAI API.

### Memory Connectors

#### JDBC Memory Connectors

Provides a memory connector that can be used to interact with a JDBC database.
- `semantickernel-connectors-memory-sqlite`
- `semantickernel-connectors-memory-postgresql`
- `semantickernel-connectors-memory-mysql`

`semantickernel-connectors-memory-azurecognitivesearch`
: Provides a memory connector for using Azure Cognitive Search as the memory provider for an application.

### Miscellaneous Packages

`semantickernel-planners`
: Implementations of various planners that can be used in the execution of semantic functions.

`semantickernel-plugin-core`
: Several example plugins, many of which are used in the samples.

`semantickernel-gpt3-tokenizer`
: A tokenizer that can be used to tokenize text for use with GPT-3. Can be used to estimate cost.


## Example Configurations

### Example: OpenAI + SQLite

POM XML for a simple project that uses OpenAI for text or chat completion with an SQLite database as the memory provider.

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

### Example: Planner using Open AI + Cognitive Search

The POM XML content for a project that uses Open AI for planning, using Azure Cognitive Search as the memory provider.

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


