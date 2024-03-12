autoload -U +X bashcompinit && bashcompinit
zmodload -i zsh/parameter
if ! (( $+functions[compdef] )) ; then
    autoload -U +X compinit && compinit
fi

_python_argcomplete() {
    local prefix=
    if [[ $COMP_LINE == 'gcloud '* ]]; then
        if [[ $3 == ssh  && $2 == *@* ]] ;then
            # handle ssh user@instance specially
            prefix=${2%@*}@
            COMP_LINE=${COMP_LINE%$2}"${2#*@}"
        elif [[ $2 == *'='* ]] ; then
            # handle --flag=value
            prefix=${2%=*}'='
            COMP_LINE=${COMP_LINE%$2}${2/'='/' '}
        fi
    fi
    local IFS=''
    COMPREPLY=( $(IFS="$IFS"                   COMP_LINE="$COMP_LINE"                   COMP_POINT="$COMP_POINT"                   _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS"                   _ARGCOMPLETE=1                   "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
        return
    fi
    # if one completion without a trailing space, add the space
    if [[ ${#COMPREPLY[@]} == 1 && $COMPREPLY != *[=' '] ]]; then
        COMPREPLY+=' '
    fi
    if [[ $prefix != '' ]]; then
        typeset -i n
        for ((n=0; n < ${#COMPREPLY[@]}; n++));do
            COMPREPLY[$n]=$prefix${COMPREPLY[$n]}
        done
    fi
}
complete -o nospace -o default -F _python_argcomplete "gcloud"

_completer() {
    command=$1
    name=$2
    eval '[[ -n "$'"${name}"'_COMMANDS" ]] || '"${name}"'_COMMANDS="$('"${command}"')"'
    set -- $COMP_LINE
    shift
    while [[ $1 == -* ]]; do
          shift
    done
    [[ -n "$2" ]] && return
    grep -q "${name}\s*$" <<< $COMP_LINE &&
        eval 'COMPREPLY=($'"${name}"'_COMMANDS)' &&
        return
    [[ "$COMP_LINE" == *" " ]] && return
    [[ -n "$1" ]] &&
        eval 'COMPREPLY=($(echo "$'"${name}"'_COMMANDS" | grep ^'"$1"'))'
}

unset bq_COMMANDS
_bq_completer() {
    _completer "CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1 bq help | grep '^[^ ][^ ]*  ' | sed 's/ .*//'" bq
}

complete -o default -F _bq_completer bq
complete -o nospace -F _python_argcomplete gsutil

