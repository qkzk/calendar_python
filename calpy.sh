#!/bin/sh

# get the current dir
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

# get the message
if [[ $# > 1 ]]; then
  #statements
  period=$1
  week=$2
  echo "Calendar Python with $period and week $week."
else
  echo "Calendar Python without arguments"
fi


# go to dir
cd /home/quentin/gdrive/dev/python/boulot_utils/calendar_python/

# activate
source venv/bin/activate

# exec python script
if [[ $# > 0]]; then
  python3 calendar_python.py $period $week
else
  python3 calendar_python.py
fi

# back to the directory we came from
cd $SCRIPTPATH
