# Python & Go CLI Project

This project is a command-line interface (CLI) application that integrates Python and Go-based tools for task management, log fetching, and a task scheduler dashboard.

## Project Overview

The project provides a unified interface to manage tasks, fetch logs, and schedule tasks through a web-based dashboard. It consists of:

* **Python CLI (Task Manager):** A Python-based command-line tool for creating, managing, and scheduling various tasks like file organization, deletion, email sending, gold rate fetching, file conversion, and file compression.
* **Go CLI (Log Fetcher):** A Go-based command-line tool for fetching logs.
* **Task Scheduler Dashboard:** A web-based user interface built with Flask for scheduling and monitoring tasks.

├── .gitignore
├── LICENSE
├── README.md
├── go_cli
    └── main.go
├── main_menu.py
└── python_cli
    ├── app.py
    ├── requirements.txt
    ├── task_manager.py
    └── templates
        ├── home.html
        └── index.html

## Setup Instructions

1.  **Clone the Repository:**

    ```bash
    git clone <repository-url>
    cd project_root
    ```

2.  **Create and Activate Virtual Environment (For Python CLI):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate     # On Windows
    ```

3.  **Install Python Dependencies:**

    ```bash
    pip install -r python_cli/requirements.txt
    ```

4.  **Compile the Go CLI (Log Fetcher):**

    ```bash
    cd go_cli
    go build -o log_fetcher
    cd ..
    ```

5.  **Running the Application:**

    To start the project, run the `main_menu.py` script:

    ```bash
    python main_menu.py
    ```

## Features

* **Task Manager (Python CLI):**
    * Handles task creation, scheduling, and management.
    * Provides a command-line interface for various tasks:
        * **File Organization:** Organizes files into directories based on their extensions.
        * **File Deletion:** Deletes files based on age and format.
        * **Email Sending:** Sends emails with support for attachments and processing email lists from CSV/XLSX files.
        * **Gold Rate Fetching:** Fetches gold rates from a website.
        * **File Conversion:** Converts files between different formats (e.g., txt to csv, txt to pdf, csv to xlsx, docx to pdf).
        * **File Compression:** Compresses files into zip or tar archives.
    * Uses `APScheduler` for task scheduling.
    * Logs task execution details to `task_manager.log` and MongoDB.
* **Go CLI (Log Fetcher):**
    * Fetches logs using a Go-based command-line tool.
    * Provides command line flags for configuring log fetcher.
* **Task Scheduler Dashboard:**
    * Web-based user interface using Flask.
    * Allows scheduling and monitoring tasks through a web browser.
    * Runs on http://127.0.0.1:5000/
* **Logging:**
    * Maintains logs of executed tasks in `task_manager.log` and MongoDB.
* **File Handling:**
    * Supports CSV and Excel file processing (`emails.csv`, `gold_rates.xlsx`).
    * Supports JSON file processing (`scheduled_tasks.json`).
    * Supports text file processing (`message.txt`).
* **Environment Configuration:**
    * Uses `.env` for secure settings.

## How to Use

1.  **Run the main menu:**

    ```bash
    python main_menu.py
    ```

2.  **Choose an option:**

    * `1`: Launch the Python CLI task manager (`task_manager.py`). This will open a new command prompt with the task manager help.
    * `2`: Launch the Go CLI log fetcher (`go_cli/main.go`). This will open a new command prompt with the go program help.
    * `3`: Start the Flask web UI (`app.py`) at `http://127.0.0.1:5000/`. This will open a new command prompt with the flask server running.
    * `4`: Exit the application.

### Using the Python CLI (Task Manager)

(Detailed CLI usage remains the same as in the previous response)

### Using the Flask Web UI

The Flask web UI provides a convenient way to manage scheduled tasks through a web browser.

1.  **Start the Flask app:**
    * From the main menu, choose option `3`.
    * Open your web browser and navigate to `http://127.0.0.1:5000/`.

2.  **Adding Tasks:**
    * Navigate to the "Manage Tasks" page from the home page.
    * Fill in the task details in the form on the `index.html` page.
    * Click the "Add Task" button.
    * The task will be added to the scheduler.

3.  **Removing Tasks:**
    * Navigate to the "Manage Tasks" page.
    * On the `index.html` page, click the "Remove Task" button.
    * Enter the task name and click "Remove Task".
    * The task will be removed from the scheduler.

4.  **Uploading Files:**
    * For the `send_email` task, you can upload recipient lists and attachments using the file upload fields.
    * Uploaded files are stored in the `python_cli/uploads/` directory.

### HTML templates details

* **home.html:**
    * This page provides an overview of the available task types.
    * It contains a list of tasks with descriptions.
    * It includes a link to the "Manage Tasks" page (`/index`).
* **index.html:**
    * This page allows users to add, list, and remove tasks.
    * It includes a form for adding new tasks with various input fields based on the selected task type.
    * It displays a list of scheduled tasks.
    * It includes a form for removing tasks.

## Contribution

Feel free to contribute by submitting issues or pull requests.

## License

This project is licensed under the terms of the LICENSE file.

## Environment Variables

(Environment variable details remain the same as in the previous response)

## Logging

(Logging details remain the same as in the previous response)

## Task Scheduler

(Task scheduler details remain the same as in the previous response)

## File Handling

(File handling details remain the same as in the previous response)

## Flask App Details

(Flask App Details remain the same as in the previous response)

## Testing

(This section will be completed if you have tests)

## Security

(Security details remain the same as in the previous response)

## Platform Specifics

(Platform specifics details remain the same as in the previous response)
## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_KEY`

`ANOTHER_API_KEY`


## Feedback

If you have any feedback, please reach out to us at fake@fake.com


## Screenshots

![App Screenshot](https://via.placeholder.com/468x300?text=App+Screenshot+Here)


## Running Tests

To run tests, run the following command

```bash
  npm run test
```

