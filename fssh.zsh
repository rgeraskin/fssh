function fssh() {

  if [ ${#*[@]} -eq 2 ]; then
    client=( "--client" $argv[1] )
    host=$argv[2]
  else
    host=$argv[1]
  fi

  echo "Composing host string..."
  BUFFER="$(ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=ignore ~/.oh-my-zsh/custom/plugins/fssh/inventory.py --inventory $FSSH_INVENTORY $client[1] $client[2] --string ${host} ) # $host"
  print -z "$BUFFER"
}
zle -N fssh

function _fssh(){
  local state

  if [ -z "${FSSH_COMPLETION}" ]; then
    FSSH_COMPLETION=clients
  fi

  _arguments \
    '1: :->client_or_host'\
    '2: :->host_of_client'

  case $state in
    (client_or_host) compadd $(ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=ignore ~/.oh-my-zsh/custom/plugins/fssh/inventory.py --inventory $FSSH_INVENTORY --completion $FSSH_COMPLETION) ;;
    (host_of_client) compadd $(ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=ignore ~/.oh-my-zsh/custom/plugins/fssh/inventory.py --inventory $FSSH_INVENTORY --client $words[2] --completion hosts) ;;
  esac
}
compdef _fssh fssh
