import os

old_path = os.getcwd()

print(f"current directory {old_path}")

os.chdir("/home/quentin/Downloads")

new_dir = os.getcwd()

print(f"current directory {new_dir}")

os.chdir(old_path)

print(f"changed back to {os.getcwd()}")
