#!/bin/bash

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            file="$2"
            shift # past argument
            shift # past value
        ;;
        -p|--propsFile)
            propsFile="$2"
            shift # past argument
            shift # past value
        ;;
        -b|--buildAndRevisionNumber)
            buildAndRevisionNumber="$2"
            shift # past argument
            shift # past value
        ;;
        -*|--*)
            echo "Unknown option $1"
            exit 1
        ;;
        *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
        ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [ -z "$file" ]; then
    echo "ERROR: Parameter file (-f|--file) not provided"
    exit 1;
elif [ ! -f "$file" ]; then
    echo "ERROR: file ${file} not found"
    exit 1;
fi

if [ -n "$(cat $file | grep -i "<IsPackable>false</IsPackable>")" ]; then
    echo "Project is marked as NOT packable - skipping."
    exit 0;
fi
    
if [ -z "$propsFile" ]; then
    echo "ERROR: Parameter propsFile (-f|--file) not provided"
    exit 1;
elif [ ! -f "$propsFile" ]; then
    echo "ERROR: propsFile ${file} not found"
    exit 1;
fi

if [ -z "$buildAndRevisionNumber" ]; then
    echo "ERROR: Parameter buildAndRevisionNumber (-b|--buildAndRevisionNumber) not provided"
    exit 1;
fi

propsVersionString=$(cat $propsFile | grep -i "<Version>");
regex="<Version>([0-9.]*)<\/Version>"
if [[ $propsVersionString =~ $regex ]]; then
  propsVersion=${BASH_REMATCH[1]}
else
  echo "ERROR: Version tag not found in propsFile"
  exit 1;
fi

if [ -z "$propsVersion" ]; then
    echo "ERROR: Version tag not found in propsFile"
    exit 1;
elif [[ ! "$propsVersion" =~ ^0.* ]]; then
    echo "ERROR: Version expected to start with 0. Actual: ${propsVersion}"
    exit 1;
fi

fullVersionString="${propsVersion}.${buildAndRevisionNumber}-preview"

if [[ ! "$fullVersionString" =~ ^0.* ]]; then
    echo "ERROR: Version expected to start with 0. Actual: ${fullVersionString}"
    exit 1;
fi

echo "==== Project: ${file} ====";
echo "propsFile = ${propsFile}"
echo "buildAndRevisionNumber = ${buildAndRevisionNumber}"
echo "version prefix from propsFile = ${propsVersion}"
echo "full version string: ${fullVersionString}"

versionInProj=$(cat $file | grep -i "<Version>");
if [ -n "$versionInProj" ]; then
    # Version tag already exists in the csproj. Let's replace it.
    echo "Updating version tag..."
    content=$(cat $file | sed --expression="s/<Version>\([0-9]*.[0-9]*\)<\/Version>/<Version>$fullVersionString<\/Version>/g");
else
    # Version tag not found in the csproj. Let's add it.
    echo "Project is packable - adding version tag..."
    content=$(cat $file | sed --expression="s/<\/Project>/<PropertyGroup><Version>$fullVersionString<\/Version><\/PropertyGroup><\/Project>/g");
fi

if [ $? -ne 0 ]; then exit 1; fi
echo "$content" && echo "$content" > $file;
if [ $? -ne 0 ]; then exit 1; fi

echo "DONE";
echo "";
