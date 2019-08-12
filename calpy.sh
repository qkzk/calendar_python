#!/bin/sh

# get the current dir
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

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
cd /home/quentin/gdrive/dev/python/boulot_utils/calendar_python/

# activate virtual environnement
source venv/bin/activate

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
cd $SCRIPTPATH
