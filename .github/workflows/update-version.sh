#!/bin/bash

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

echo "file = ${file}"
echo "buildAndRevisionNumber = ${buildAndRevisionNumber}"

echo "====${file}====";
versionString=$(cat $file | grep -i "<Version>");
if [ -n "$versionString" ]; then
    echo "Updating version tag..."
    content=$(cat $file | sed --expression="s/<Version>\([0-9]*.[0-9]*\)<\/Version>/<Version>\1.$buildAndRevisionNumber-preview<\/Version>/g");
else
    if [ -n "$(cat $file | grep -i "<IsPackable>false</IsPackable>")" ]; then
        echo "Project is marked as NOT packable - skipping."
        continue;
    fi
    echo "Project is packable - adding version tag..."
    content=$(cat $file | sed --expression="s/<\/Project>/<PropertyGroup><Version>1.0.$buildAndRevisionNumber-preview<\/Version><\/PropertyGroup><\/Project>/g");
fi

if [ $? -ne 0 ]; then exit 1; fi
echo "$content" && echo "$content" > $file;
if [ $? -ne 0 ]; then exit 1; fi
