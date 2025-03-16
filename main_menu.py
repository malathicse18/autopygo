import os
import subprocess

def launch_command(command):
    """Launch command in a new terminal window based on the OS"""
    if os.name == "nt":  # Windows
        subprocess.Popen(f'start cmd /k "{command}"', shell=True)
    else:  # Linux
        subprocess.Popen(["xterm", "-e", f"bash -c '{command}; exec bash'"])

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        print("\nMenu:")
        print("1. Python CLI (Task Manager)")
        print("2. Go CLI (Log Fetcher)")
        print("3. Task Scheduler Dashboard")
        print("4. Exit")

        choice = input("Enter your choice (1/2/3/4): ")

        if choice == "1":
            print("Launching Python CLI...")
            python_cli_dir = os.path.join(root_dir, "python_cli")
            help_command = f'cd {python_cli_dir} && python3 task_manager.py --help'
            launch_command(help_command)
        elif choice == "2":
            print("Launching Go CLI...")
            go_cli_dir = os.path.join(root_dir, "go_cli")
            help_command = f'cd {go_cli_dir} && go run main.go -h'
            launch_command(help_command)
        elif choice == "3":
            print("Launching Task Scheduler Dashboard...")
            print("http://127.0.0.1:5000/")
            python_cli_dir = os.path.join(root_dir, "python_cli")
            ui_command = f'cd {python_cli_dir} && python3 app.py'
            launch_command(ui_command)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
