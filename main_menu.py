import os
import subprocess

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        print("\nMenu:")
        print("1. Python CLI (Task Manager)")
        print("2. Go CLI (Log Fetcher)")
        print("3. Exit")

        choice = input("Enter your choice (1/2/3): ")

        if choice == "1":
            print("Launching Python CLI...")
            python_cli_dir = os.path.join(root_dir, "python_cli")
            subprocess.Popen(f'start cmd /k "cd {python_cli_dir} && python task_manager.py"', shell=True)
            break
        elif choice == "2":
            print("Launching Go CLI...")
            go_cli_dir = os.path.join(root_dir, "go_cli")
            subprocess.Popen(f'start cmd /k "cd {go_cli_dir} && go_cli"', shell=True)
            break
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()