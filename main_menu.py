import os
import subprocess
import platform

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os_type = platform.system()  # Detect OS type

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
            python_cmd = "python3" if os_type != "Windows" else "python"
            help_command = f'cd {python_cli_dir} && {python_cmd} task_manager.py --help'

            try:
                if os_type == "Windows":
                    subprocess.Popen(f'start cmd /k "{help_command}"', shell=True)
                else:
                    subprocess.Popen(["xterm", "-fa", "fixed", "-fs", "20", "-e", f"bash -c '{help_command}; exec bash'"])
            except Exception as e:
                print(f"Failed to launch Python CLI: {e}")

        elif choice == "2":
            print("Launching Go CLI...")
            go_cli_dir = os.path.join(root_dir, "go_cli")
            help_command = f'cd {go_cli_dir} && go run main.go -h'

            try:
                if os_type == "Windows":
                    subprocess.Popen(f'start cmd /k "{help_command}"', shell=True)
                else:
                    subprocess.Popen(["xterm", "-fa", "fixed", "-fs", "20", "-e", f"bash -c '{help_command}; exec bash'"])
            except Exception as e:
                print(f"Failed to launch Go CLI: {e}")

        elif choice == "3":
            print("Launching Task Scheduler Dashboard...")
            print("http://127.0.0.1:5000/")
            python_cli_dir = os.path.join(root_dir, "python_cli")
            python_cmd = "python3" if os_type != "Windows" else "python"
            ui_command = f'cd {python_cli_dir} && {python_cmd} app.py'

            try:
                if os_type == "Windows":
                    subprocess.Popen(f'start cmd /k "{ui_command}"', shell=True)
                else:
                    # subprocess.Popen(["xterm", "-e", f"bash -c '{ui_command}; exec bash'"]) 
                    #subprocess.Popen(["xterm", "-fa", "Arial", "-fs", "30", "-e", f"bash -c '{ui_command}; exec bash'"])
                    subprocess.Popen(["xterm", "-fa", "fixed", "-fs", "20", "-e", f"bash -c '{ui_command}; exec bash'"])
            except Exception as e:
                print(f"Failed to launch Task Scheduler Dashboard: {e}")

        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
