# Semantic Kernel for Java Packages

The Semantic Kernel has the packages below, all are under the groupId `com.microsoft.semantic-kernel`, and can be imported
to maven.

```xml
    <dependency>
        <groupId>com.microsoft.semantic-kernel</groupId>
        <artifactId>semantickernel-api</artifactId>
    </dependency>
```

A BOM is provided that can be used to define the versions of all Semantic Kernel packages.

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
: A Maven project BOM that can be used to define the versions of all Semantic Kernel packages.

`semantickernel-api`
: Package that defines the core public API for the Semantic Kernel for a Maven project.

## Services

`semantickernel-aiservices-openai`
: Provides a connector that can be used to interact with the OpenAI API.

## Example Configurations

### Example: OpenAI + SQLite

POM XML for a simple project that uses OpenAI.

```xml

<project>
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
            <artifactId>semantickernel-connectors-ai-openai</artifactId>
        </dependency>
    </dependencies>
</project>
```



