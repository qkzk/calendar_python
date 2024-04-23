#! /usr/bin/python3


if __name__ == "__main__":
    import os

    old_path = os.getcwd()
    os.chdir("/home/quentin/gclem/dev/python/boulot_utils/calpy_branches")

    from src import create_or_update_week_events

    create_or_update_week_events()
    os.chdir(old_path)
