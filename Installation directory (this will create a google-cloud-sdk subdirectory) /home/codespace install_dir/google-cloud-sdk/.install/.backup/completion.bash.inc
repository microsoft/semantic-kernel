_python_argcomplete() {
    local IFS=''
    local prefix=
    typeset -i n
    (( lastw=${#COMP_WORDS[@]} -1))
    if [[ ${COMP_WORDS[lastw]} == --*=* ]]; then
        # for bash version 3.2
        flag=${COMP_WORDS[lastw]%%=*}
        set -- "$1" "$2" '='
    elif [[ $3 == '=' ]]; then
      flag=${COMP_WORDS[-3]}
    fi
    if [[ $3 == ssh  && $2 == *@* ]] ;then
        # handle ssh user@instance specially
        prefix=${2%@*}@
        COMP_LINE=${COMP_LINE%$2}"${2#*@}"
    elif [[ $3 == '=' ]] ; then
        # handle --flag=value
        prefix=$flag=$2
        line=${COMP_LINE%$prefix};
        COMP_LINE=$line${prefix/=/ };
        prefix=
    fi
    if [[ $2 == *,* ]]; then
          # handle , separated list
          prefix=${2%,*},
          set -- "$1" "${2#$prefix}" "$3"
          COMP_LINE==${COMP_LINE%$prefix*}$2
    fi
    # Treat --flag=<TAB> as --flag <TAB> to work around bash 4.x bug
    if [[ ${COMP_LINE} == *=  && ${COMP_WORDS[-2]} == --* ]]; then
        COMP_LINE=${COMP_LINE%=}' '
    fi
    COMPREPLY=( $(IFS="$IFS"                   COMP_LINE="$COMP_LINE"                   COMP_POINT="$COMP_POINT"                   _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS"                   _ARGCOMPLETE=1                   "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
        return
    fi
    if [[ $prefix != '' ]]; then
        for ((n=0; n < ${#COMPREPLY[@]}; n++)); do
            COMPREPLY[$n]=$prefix${COMPREPLY[$n]}
        done
    fi
    for ((n=0; n < ${#COMPREPLY[@]}; n++)); do
        match=${COMPREPLY[$n]%' '}
        if [[ $match != '' ]]; then
            COMPREPLY[$n]=${match//? /' '}' '
        fi
    done
    # if flags argument has a single completion and ends in  '= ', delete ' '
    if [[ ${#COMPREPLY[@]} == 1 && ${COMPREPLY[0]} == -* &&
          ${COMPREPLY[0]} == *'= ' ]]; then
        COMPREPLY[0]=${COMPREPLY[0]%' '}
    fi
}
complete -o nospace -F _python_argcomplete "gcloud"

_completer() {
    command=$1
    name=$2
    eval '[[ "$'"${name}"'_COMMANDS" ]] || '"${name}"'_COMMANDS="$('"${command}"')"'
    set -- $COMP_LINE
    shift
    while [[ $1 == -* ]]; do
          shift
    done
    [[ $2 ]] && return
    grep -q "${name}\s*$" <<< $COMP_LINE &&
        eval 'COMPREPLY=($'"${name}"'_COMMANDS)' &&
        return
    [[ "$COMP_LINE" == *" " ]] && return
    [[ $1 ]] &&
        eval 'COMPREPLY=($(echo "$'"${name}"'_COMMANDS" | grep ^'"$1"'))'
}

unset bq_COMMANDS
_bq_completer() {
    _completer "CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1 bq help | grep '^[^ ][^ ]*  ' | sed 's/ .*//'" bq
}

complete -F _bq_completer bq
complete -o nospace -F _python_argcomplete gsutil
