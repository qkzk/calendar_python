#!/bin/zsh

# get the current dir
CURRPATH="$( cd "$(dirname "$0")" ; pwd -P )"
SCRIPTATH="/home/quentin/gdrive/dev/python/boulot_utils/calendar_python"
VENVPATH="/home/quentin/ntfs/venv/calendar_python_venv"

# get the message
if [[ $# > 1 ]]; then
  #statements
  echo "Calendar Python with period and week."
else
  echo "Calendar Python without arguments"
fi

# new dir without venv
cd $VENVPATH

# activate virtual environnement
source venv/bin/activate

# go where the script is
cd $SCRIPTATH

# exec python script
if [[ $# > 1 ]]; then
  # without
  python calendar_python.py "$@"
else
  python calendar_python.py
fi

# deactivate virtual environnement
deactivate

# back to the directory we came from
cd $CURRPATH
