# AutoPyGo: Automated Task Management

AutoPyGo is a versatile application that combines Python and Go tools to automate various tasks, fetch logs, and provide a user-friendly web-based task scheduler dashboard.

## Overview

AutoPyGo offers:

* **Python CLI (Task Manager):** Automate tasks like file organization, email sending, and more via the command line.
* **Go CLI (Log Fetcher):** Efficiently retrieve logs using a fast Go-based tool.
* **Web Dashboard:** Schedule, monitor, and manage automated tasks through an intuitive web interface.

## Getting Started

1.  **Clone the Repository:**

    ```bash
    git clone <repository-url>
    cd autopygo
    ```

2.  **Set up Python Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate     # Windows
    pip install -r python_cli/requirements.txt
    ```

3.  **Build Go CLI:**

    ```bash
    cd go_cli
    go mod go_cli
    go mod tidy
    ```

4.  **Run the Application:**

    ```bash
    python main_menu.py
    ```

## How to Use

1.  **Run the Main Menu:**

    ```bash
    python main_menu.py
    ```

2.  **Choose an Option:**

    * `1`: Launch the Python CLI task manager.
    * `2`: Launch the Go CLI log fetcher.
    * `3`: Start the web dashboard (http://127.0.0.1:5000/).
    * `4`: Exit.

### Python CLI (Task Manager)

* Utilize commands to automate file organization, email tasks, and more.
* Refer to the command-line help for specific instructions.

### Web Dashboard

1.  **Start the Dashboard:** Select option `3` from the main menu.
2.  **Add Tasks:** Complete the form on the "Manage Tasks" page.
3.  **Remove Tasks:** Use the remove task feature on the "Manage Tasks" page.
4.  **List Tasks:** List All Scheduled Tasks
5.  **Upload Files:** Upload files for email-related tasks.

### Web Page Descriptions

* **home.html:** Provides an overview of available automated tasks.
* **index.html:** Enables adding, listing, and removing automated tasks.

## Features

* **Automated Task Management:** Schedule and manage a variety of automated tasks.
* **Efficient Log Fetching:** Quickly retrieve logs.
* **User-Friendly Web Interface:** Easy-to-use task scheduler.
* **Task Logging:** Track execution of automated tasks.
* **Flexible File Handling:** Process CSV, Excel, and text files.

## Environment Variables

Add your config details to a `.env` file within the `python_cli`and go_cli folder:

SENDER_EMAIL=dummyemail@example.com  [python_cli]
SENDER_PASSWORD=dummypassword123     [python_cli]
MONGO_URI=mongodb://localhost:27017/ [Go and python cli]
DB_NAME=task_manager_db              [Go and python cli]
COLLECTION_NAME=logs                 [Go and python cli]
