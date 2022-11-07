#!/bin/zsh

# get the current dir
CURRPATH="$( cd "$(dirname "$0")" ; pwd -P )"
SCRIPTATH="/home/quentin/gclem/dev/python/boulot_utils/calendar_python"

# get the message
if [[ $# > 1 ]]; then
  #statements
  echo "Calendar Python with period and week."
else
  echo "Calendar Python without arguments"
fi

# go where the script is
cd $SCRIPTATH

# exec python script
if [[ $# > 1 ]]; then
  # without
  python main.py "$@"
else
  python main.py
fi

# back to the directory we came from
cd $CURRPATH
