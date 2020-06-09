#!/bin/zsh

# get the current dir
CURRPATH="$( cd "$(dirname "$0")" ; pwd -P )"
SCRIPTATH="/home/quentin/gdrive/dev/python/boulot_utils/calendar_python"
VENVPATH="/run/media/quentin/data/venv/calendar_python_venv"

# get the message
if [[ $# > 1 ]]; then
  #statements
  period=$1
  week=$2
  echo "Calendar Python with period $period and week $week."
else
  echo "Calendar Python without arguments"
fi
#
# if [[ $# > 0 ]]; then
#   #statements
#   msg=${@}
# else
#   msg='autocommit'
# fi
# echo $msg
#
# go to dir

# old dir with venv
# cd /home/quentin/gdrive/dev/python/boulot_utils/calendar_python/

# new dir without venv
cd $VENVPATH

# activate virtual environnement
source venv/bin/activate

# go where the script is
cd $SCRIPTATH
# exec python script
if [[ $# > 1 ]]; then
  # without
  python3 calendar_python.py $period $week
else
  python3 calendar_python.py
fi

# deactivate virtual environnement
deactivate

# back to the directory we came from
cd $CURRPATH
