__FSSH_DIR="${0:A:h}"

function fssh() {

  if [ ${#*[@]} -eq 2 ]; then
    client=( "--client" $argv[1] )
    host=$argv[2]
  else
    host=$argv[1]
  fi

  echo "Composing host string..."
  BUFFER="$(ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=ignore ${__FSSH_DIR}/inventory.py --inventory $FSSH_INVENTORY $client[1] $client[2] --string ${host} ) # $host"
  print -z "$BUFFER"
}
zle -N fssh
