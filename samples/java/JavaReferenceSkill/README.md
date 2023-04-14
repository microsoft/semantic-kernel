# Java Reference Skill gRPC Server
This is a reference implementation of a gRPC server for the Java Reference Skill. It is intended to be used as a starting point for developers who want to create their own gRPC server for the Java Reference Skill.

## Prerequisites
* Java 17
* Maven

## Build
To build the project, run the following command:
```
mvn clean package
```
To generate the gRPC classes, run the following command:
```
mvn protobuf:compile
```

## Run
To run the project, run the following command:
```
java -jar ./target/JavaReferenceSkill-1.0-SNAPSHOT-jar-with-dependencies.jar
```

