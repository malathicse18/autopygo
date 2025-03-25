# ```python
import os
import re
import shutil
import time
import logging
import json
import threading
import argparse
import requests
import pandas as pd
import smtplib
import zipfile
import tarfile
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pymongo import MongoClient
from docx import Document
from fpdf import FPDF
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

class TaskManager:
    def __init__(self):
        """Initialize TaskManager with logging, MongoDB, and scheduler."""
        # Logging Configuration
        logging.basicConfig(
            filename="task_manager.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        mongo_host = os.environ.get("MONGO_HOST", "localhost")  # Default to localhost
        mongo_port = os.environ.get("MONGO_PORT", "27017")
        mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"

        client = MongoClient(mongo_uri)
        db = client["task_manager_db"]
        logs_collection = db["logs"]

        # Scheduler Configuration
        self.scheduler = BackgroundScheduler()

        # Task Storage File
        self.tasks_file = "scheduled_tasks.json"

        # File Types for Organization
        self.file_types = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
            "Videos": [".mp4", ".mkv", ".flv", ".mov", ".avi", ".wmv"],
            "Documents": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
            "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
            "Executables": [".exe", ".msi", ".bat", ".sh"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php"],
            "Data": [".csv", ".json", ".xml", ".sql", ".db"],
        }

        # Load and schedule existing tasks
        self.load_and_schedule_tasks()

    def log_to_mongodb(self, task_name, details, status, level="INFO"):
        """Log actions to MongoDB."""
        log_entry = {
            "task_name": task_name,
            "details": details,
            "status": status,
            "level": level,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.logs_collection.insert_one(log_entry)

    def load_tasks(self):
        """Load tasks from the JSON file."""
        try:
            with open(self.tasks_file, "r") as f:
                tasks = json.load(f)
                return tasks if isinstance(tasks, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_tasks(self, tasks):
        """Save tasks to the JSON file."""
        with open(self.tasks_file, "w") as f:
            json.dump(tasks, f, indent=4)

    def organize_files(self, directory):
        """Organize files in the given directory based on their extensions."""
        try:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            for file in files:
                file_extension = os.path.splitext(file)[1].lower()
                category = "Others"
                for folder_name, extensions in self.file_types.items():
                    if file_extension in extensions:
                        category = folder_name
                        break
                category_folder = os.path.join(directory, category)
                if not os.path.exists(category_folder):
                    os.makedirs(category_folder)
                shutil.move(os.path.join(directory, file), os.path.join(category_folder, file))
                self.logger.info(f"Moved '{file}' to '{category}' folder.")
                self.log_to_mongodb("organize_files", {"file": file, "category": category}, "File moved")
            self.logger.info(f"File organization in '{directory}' completed successfully.")
            self.log_to_mongodb("organize_files", {"directory": directory}, "Organization completed")
        except Exception as e:
            self.logger.error(f"Error organizing files in '{directory}': {e}")
            self.log_to_mongodb("organize_files", {"directory": directory, "error": str(e)}, "Error", level="ERROR")

    def delete_files(self, directory, age_days, formats):
        """Delete files older than `age_days` and matching `formats`."""
        try:
            cutoff_time = time.time() - (age_days * 86400)
            deleted_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[1].lower()
                    if file_extension in formats and os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        self.logger.info(f"Deleted file: {file_path}")
            if deleted_files:
                self.log_to_mongodb("delete_files", {"deleted_files": deleted_files}, "Files deleted")
            else:
                self.logger.info("No files deleted.")
                self.log_to_mongodb("delete_files", {}, "No files deleted")
        except Exception as e:
            self.logger.error(f"Error deleting files: {e}")
            self.log_to_mongodb("delete_files", {"directory": directory, "age_days": age_days, "formats": formats}, f"Error: {e}", level="ERROR")

    def send_email(self, recipient_email, subject, message, attachments=None):
        """Send email(s) with optional attachments."""
        SENDER_EMAIL = os.getenv("SENDER_EMAIL")
        SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            self.logger.error("Missing email credentials in .env file.")
            return False

        # Log the email details (Improved logging)
        self.logger.info(f"Sending email(s) with the following details:")
        self.logger.info(f"  To: {recipient_email}")
        self.logger.info(f"  Subject: {subject}")
        self.logger.info(f"  Message: {message}")
        self.logger.info(f"  Attachments: {attachments}")

        if isinstance(recipient_email, str) and (recipient_email.endswith(".csv") or recipient_email.endswith(".xlsx")):
            # Handle CSV or XLSX file
            try:
                if recipient_email.endswith(".csv"):
                    df = pd.read_csv(recipient_email)
                elif recipient_email.endswith(".xlsx"):
                    df = pd.read_excel(recipient_email)
                else:
                    raise ValueError("Unsupported email list format. Only CSV and XLSX are supported.")

                if os.path.isfile(message):
                    with open(message, "r") as f:
                        message_template = f.read()
                else:
                    message_template = message

                for index, row in df.iterrows():
                    email = row.get("email")
                    name = row.get("name", "")  # Get name, default to empty string if not found
                    if not self.is_valid_email(email):
                        self.logger.warning(f"Invalid email: {email}")
                        continue
                    msg_content = message_template.replace("{name}", name)
                    if self._send_single_email([email], subject, msg_content, attachments):
                        self.logger.info(f"Email sent to {email}")
                    else:
                        self.logger.error(f"Email failed to {email}")

            except Exception as e:
                self.logger.error(f"Error sending emails from file: {e}")
                return False

        else:
            # Handle list or string of email addresses
            if isinstance(recipient_email, str):
                recipient_email = [email.strip() for email in recipient_email.split(",")]
            elif not isinstance(recipient_email, list):
                self.logger.error("Invalid recipient_email format. Expected a string or list.")
                return False

            # Filter out invalid email addresses
            valid_emails = [email for email in recipient_email if self.is_valid_email(email)]
            invalid_emails = [email for email in recipient_email if not self.is_valid_email(email)]

            if invalid_emails:
                self.logger.warning(f"Invalid email addresses: {invalid_emails}")

            if not valid_emails:
                self.logger.error("No valid email addresses found.")
                return False

            for email in valid_emails:
                # Simple name extraction (you might need a more robust method)
                name = email.split("@")[0]
                msg_content = message.replace("{name}", name)

                if self._send_single_email([email], subject, msg_content, attachments):
                    self.logger.info(f"Email sent to {email}")
                else:
                    self.logger.error(f"Failed to send email to {email}")

    def _send_single_email(self, recipient_emails, subject, message, attachments=None):
        """Helper method to send a single email to a list of recipients."""
        SENDER_EMAIL = os.getenv("SENDER_EMAIL")
        SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            self.logger.error("Missing email credentials in .env file.")
            return False

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(recipient_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        if attachments:
            for attachment in attachments:
                try:
                    with open(attachment, "rb") as file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment)}")
                    msg.attach(part)
                except FileNotFoundError:
                    self.logger.error(f"Attachment '{attachment}' not found.")

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_emails, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient_emails}: {e}")
            return False

    def is_valid_email(self, email):
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    def get_gold_rate(self):
        """Scrape gold rates from a website and store in an Excel file."""
        url = "https://www.bankbazaar.com/gold-rate-tamil-nadu.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            self.logger.error(f"Error fetching gold rates: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        price_span = soup.find("span", class_="white-space-nowrap")
        if price_span:
            gold_price = price_span.get_text(strip=True)
            self.logger.info(f"22k India Gold rate: {gold_price}")

            excel_file = "gold_rates.xlsx"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            try:
                if os.path.exists(excel_file):
                    df = pd.read_excel(excel_file)
                    new_row = {"Timestamp": timestamp, "22k India Gold Price": gold_price}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_excel(excel_file, index=False)
                else:
                    df = pd.DataFrame({"Timestamp": [timestamp], "22k India Gold Price": [gold_price]})
                    df.to_excel(excel_file, index=False)
            except Exception as e:
                self.logger.error(f"Error writing to excel file: {e}")

            self.logger.info(f"Gold rate stored in {excel_file}")
            self.log_to_mongodb("get_gold_rate", {"gold_price": gold_price, "timestamp": timestamp}, "Gold rate stored")

            return gold_price
        else:
            self.logger.error("Gold price not found.")
            return None

    def convert_file(self, input_dir, output_dir, input_format, output_format):
        """Convert files in the input directory to the output directory."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for filename in os.listdir(input_dir):
                if filename.lower().endswith(f".{input_format}"):
                    input_path = os.path.join(input_dir, filename)
                    output_filename = os.path.splitext(filename)[0] + f".{output_format}"
                    output_path = os.path.join(output_dir, output_filename)

                    try:
                        if input_format == "txt" and output_format == "csv":
                            with open(input_path, "r") as f:
                                content = f.read()
                            with open(output_path, "w") as f:
                                f.write(content.upper())
                        elif input_format == "txt" and output_format == "pdf":
                            with open(input_path, "r") as f:
                                content = f.read()
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            pdf.multi_cell(0, 10, content)
                            pdf.output(output_path)
                        elif input_format == "csv" and output_format == "xlsx":
                            df = pd.read_csv(input_path)
                            df.to_excel(output_path, index=False)
                        elif input_format == "docx" and output_format == "pdf":
                            doc = Document(input_path)
                            pdf = FPDF()
                            pdf.add_page()
                            for para in doc.paragraphs:
                                pdf.set_font("Arial", size=12)
                                pdf.multi_cell(0, 10, para.text)
                            pdf.output(output_path)
                        else:
                            raise ValueError("Unsupported conversion format")

                        self.logger.info(f"Converted '{input_path}' to '{output_path}'")
                        self.log_to_mongodb("convert_file", {"input": input_path, "output": output_path}, "Conversion successful")

                    except Exception as e:
                        self.logger.error(f"Error converting file '{input_path}': {e}")
                        self.log_to_mongodb("convert_file", {"input": input_path, "output": output_path}, f"Error: {e}", level="ERROR")

            self.logger.info(f"Converted files from '{input_dir}' to '{output_dir}'")
            self.log_to_mongodb("convert_file", {"input_dir": input_dir, "output_dir": output_dir}, "Conversion successful")

        except Exception as e:
            self.logger.error(f"Error converting files in directory: {e}")
            self.log_to_mongodb("convert_file", {"input_dir": input_dir, "output_dir": output_dir}, f"Error: {e}", level="ERROR")
    def compress_files(self, directory, output_dir, compression_format):
        """Compress files in a directory, excluding the output directory."""
        try:
            os.makedirs(output_dir, exist_ok=True)

            if compression_format == "zip":
                output_path = os.path.join(output_dir, os.path.basename(directory) + ".zip")
                with zipfile.ZipFile(output_path, 'w') as zipf:
                    for root, _, files in os.walk(directory):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory))
            elif compression_format == "tar":
                output_path = os.path.join(output_dir, os.path.basename(directory) + ".tar")
                with tarfile.open(output_path, 'w') as tarf:
                    for filename in os.listdir(directory):
                        filepath = os.path.join(directory, filename)
                        if os.path.isfile(filepath):
                            tarf.add(filepath, arcname=filename)
            else:
                raise ValueError("Unsupported compression format")

            self.logger.info(f"Compressed '{directory}' to '{output_path}'")
            self.log_to_mongodb("compress_files", {"directory": directory, "output": output_path}, "Compression successful")
        except Exception as e:
            self.logger.error(f"Error compressing files: {e}")
            self.log_to_mongodb("compress_files", {"directory": directory, "output": output_dir}, f"Error: {e}", level="ERROR")

    def add_task(self, interval, unit, task_type, **kwargs):
        """Add a new task to the scheduler."""
        tasks = self.load_tasks()
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        new_task_details = {"interval": interval, "unit": unit, "task_type": task_type, **filtered_kwargs}

        # Check for duplicates based on relevant fields
        for task_name, existing_task_details in tasks.items():
            if (
                existing_task_details["task_type"] == new_task_details["task_type"]
                and existing_task_details["interval"] == new_task_details["interval"]
                and existing_task_details["unit"] == new_task_details["unit"]
                # Add task-specific checks here (example for organize_files):
                and (
                    task_type != "organize_files"
                    or existing_task_details.get("directory") == new_task_details.get("directory")
                )
                # Add similar checks for other task types...
                and (
                    task_type != "delete_files"
                    or (existing_task_details.get("directory") == new_task_details.get("directory") and existing_task_details.get("age_days") == new_task_details.get("age_days") and existing_task_details.get("formats") == new_task_details.get("formats"))
                )
                and (
                    task_type != "send_email"
                    or (existing_task_details.get("recipient_email") == new_task_details.get("recipient_email") and existing_task_details.get("subject") == new_task_details.get("subject") and existing_task_details.get("message") == new_task_details.get("message") and existing_task_details.get("attachments") == new_task_details.get("attachments"))
                )
                and (
                    task_type != "convert_file"
                    or (existing_task_details.get("input_dir") == new_task_details.get("input_dir") and existing_task_details.get("output_dir") == new_task_details.get("output_dir") and existing_task_details.get("input_format") == new_task_details.get("input_format") and existing_task_details.get("output_format") == new_task_details.get("output_format"))
                )
                and (
                    task_type != "compress_files"
                    or (existing_task_details.get("directory") == new_task_details.get("directory") and existing_task_details.get("output_dir") == new_task_details.get("output_dir") and existing_task_details.get("compression_format") == new_task_details.get("compression_format"))
                )
            ):
                print(f"Task Exists already {existing_task_details}. Task not added.")
                return False  # Indicate task was not added (duplicate)

        # Generate a simple task name and handle conflicts
        counter = 1
        while True:
            task_name = f"{task_type}_{counter}"
            if task_name not in tasks:
                break
            counter += 1

        trigger = IntervalTrigger(**{unit: interval})

        if task_type == "organize_files":
            self.scheduler.add_job(self.organize_files, trigger, args=[filtered_kwargs["directory"]], id=task_name)
        elif task_type == "delete_files":
            self.scheduler.add_job(self.delete_files, trigger, args=[filtered_kwargs["directory"], filtered_kwargs["age_days"], filtered_kwargs["formats"]], id=task_name)
        elif task_type == "send_email":
            attachments = filtered_kwargs.get("attachments", None)
            self.scheduler.add_job(self.send_email, trigger, args=[filtered_kwargs["recipient_email"], filtered_kwargs["subject"], filtered_kwargs["message"], attachments], id=task_name)
        elif task_type == "get_gold_rate":
            self.scheduler.add_job(self.get_gold_rate, trigger, id=task_name)
        elif task_type == "convert_file":
            self.scheduler.add_job(
                self.convert_file,
                trigger,
                args=[
                    filtered_kwargs["input_dir"],
                    filtered_kwargs["output_dir"],
                    filtered_kwargs["input_format"],
                    filtered_kwargs["output_format"],
                ],
                id=task_name,
            )
        elif task_type == "compress_files":
            self.scheduler.add_job(self.compress_files, trigger, args=[filtered_kwargs["directory"], filtered_kwargs["output_dir"], filtered_kwargs["compression_format"]], id=task_name)
        else:
            raise ValueError("Unsupported task type")

        tasks[task_name] = new_task_details
        self.save_tasks(tasks)
        self.logger.info(f"Added task '{task_name}'")
        self.log_to_mongodb("add_task", {"task_name": task_name, "details": tasks[task_name]}, "Task added")

        print(f"Task '{task_name}' added successfully.")
        print(f"Task details: {tasks[task_name]}")
        return True  # Indicate task was added successfully    
    def remove_task(self, task_name):
        """Remove a task from the scheduler."""
        tasks = self.load_tasks()
        if task_name in tasks:
            self.scheduler.remove_job(task_name)
            del tasks[task_name]
            self.save_tasks(tasks)
            self.logger.info(f"Removed task '{task_name}'")
            self.log_to_mongodb("remove_task", {"task_name": task_name}, "Task removed")
            print(f"Task '{task_name}' removed successfully.")
        else:
            self.logger.warning(f"Task '{task_name}' not found")
            self.log_to_mongodb("remove_task", {"task_name": task_name}, "Task not found", level="WARNING")

    def list_tasks(self):
        """List all scheduled tasks."""
        tasks = self.load_tasks()
        if not tasks:
            print("No tasks scheduled.")
        else:
            print("Scheduled tasks:")
            for task_name, details in tasks.items():
                filtered_details = {k: v for k, v in details.items() if v is not None}
                print(f"- {task_name}: {filtered_details}")

    def load_and_schedule_tasks(self):
        """Load and schedule tasks from the JSON file."""
        tasks = self.load_tasks()
        for task_name, details in tasks.items():
            trigger = IntervalTrigger(**{details["unit"]: details["interval"]})
            if details["task_type"] == "organize_files":
                self.scheduler.add_job(self.organize_files, trigger,args=[details["directory"]], id=task_name)
            elif details["task_type"] == "delete_files":
                self.scheduler.add_job(self.delete_files, trigger, args=[details["directory"], details["age_days"], details["formats"]], id=task_name)
            elif details["task_type"] == "send_email":
                self.scheduler.add_job(self.send_email, trigger, args=[details["recipient_email"], details["subject"], details["message"], details.get("attachments",)], id=task_name)
            elif details["task_type"] == "get_gold_rate":
                self.scheduler.add_job(self.get_gold_rate, trigger, id=task_name)
            elif details["task_type"] == "convert_file":
                self.scheduler.add_job(self.convert_file, trigger, args=[details["input_dir"], details["output_dir"], details["input_format"], details["output_format"]], id=task_name)
            elif details["task_type"] == "compress_files":
                self.scheduler.add_job(self.compress_files, trigger, args=[details["directory"], details["output_dir"], details["compression_format"]], id=task_name)

    def start_scheduler(self):
        """Start the scheduler."""
        self.scheduler.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
            self.scheduler.shutdown()


# CLI Interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python-Task Manager CLI", formatter_class=argparse.RawTextHelpFormatter)
    usage=argparse.SUPPRESS  # This line removes the "usage:" line
    # Add a custom help message
    parser.epilog = """
*** Available Services for Scheduling ***:
        - organize_files
        - delete_files
        - send_email
        - get_gold_rate
        - convert_file
        - compress_files

commands:
    add     Add a new task. 
            Example usage: python task_manager.py add -h

    remove      Remove a task. 
            Example usage: python task_manager.py remove -h

    list        List all scheduled tasks. 
            Example usage: python task_manager.py list -h

    start       Start the scheduler. 
            Example usage: python task_manager.py start -h

For more details on each commands, use the -h option with the subcommand.
    """
    # args = parser.parse_args()

    subparsers = parser.add_subparsers(dest="command",help=argparse.SUPPRESS)

    # Add Task Parser
    add_parser = subparsers.add_parser("add", help="Add a new task", formatter_class=argparse.RawTextHelpFormatter)
    add_parser.add_argument("--interval", type=int, required=True, help=argparse.SUPPRESS)
    add_parser.add_argument("--unit", type=str, required=True, choices=["seconds", "minutes", "hours", "days"], help=argparse.SUPPRESS)
    add_parser.add_argument("--task-type", type=str, required=True, choices=["organize_files", "delete_files", "send_email", "get_gold_rate", "convert_file", "compress_files"], help=argparse.SUPPRESS)
    add_parser.add_argument("--directory", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--age-days", type=int, help=argparse.SUPPRESS)
    add_parser.add_argument("--formats", nargs="*", help=argparse.SUPPRESS)
    add_parser.add_argument("--recipient-email", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--subject", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--message", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--attachments", nargs="*", help=argparse.SUPPRESS)
    add_parser.add_argument("--input-dir", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--output-dir", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--input-format", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--output-format", type=str, help=argparse.SUPPRESS)
    add_parser.add_argument("--compression-format", type=str, choices=["zip", "tar"], help=argparse.SUPPRESS)
    add_parser.epilog = """
Available tasks:

    organize_files: Organize files in a directory.
                    Organization: Files are categorized into folders based on their extensions:
                    [Images, Videos, Documents, Audio, Archives, Executables, Code, Data, Others.]

    delete_files: Delete files older than a specified age.

    send_email: Send an email.
    
    get_gold_rate: Scrape and store 22K gold rates in India.

    convert_file: Convert files in a directory. Supported conversions:
        - txt to csv
        - txt to pdf
        - csv to xlsx
        - docx to pdf
        
    compress_files: Compress files in a directory.
                    Compression Format [ZIP/TAR]   

Example usage:

    organize_files: 
                    python task_manager.py add --interval 1 --unit days --task-type organize_files --directory '/path/to/directory'

    delete_files: 
                    python task_manager.py add --interval 1 --unit days --task-type delete_files --directory '/path/to/directory' --age-days 30 --formats .txt .log

    send_email: 
                    python task_manager.py add --interval 1 --unit days --task-type send_email --recipient-email 'recipient@example.com' --subject 'Subject' --message 'Message' --attachments '/path/to/file1.txt' '/path/to/file2.pdf'

    get_gold_rate: 
                    python task_manager.py add --interval 1 --unit hours --task-type get_gold_rate

    convert_file: 
                    python task_manager.py add --interval 1 --unit days --task-type convert_file --input-dir '/path/to/input' --output-dir '/path/to/output' --input-format txt --output-format pdf

    compress_files: 
                    python task_manager.py add --interval 1 --unit days --task-type compress_files --directory '/path/to/directory' --output-dir '/path/to/output' --compression-format zip
"""

    # Remove Task Parser
    remove_parser = subparsers.add_parser("remove", help="Remove a task", formatter_class=argparse.RawTextHelpFormatter)
    remove_parser.add_argument("--task-name", type=str, required=True, help="Name of the task to remove (e.g., 'organize_files_task_1')")
    remove_parser.epilog = """
Example usage:
    
    python task_manager.py remove --task-name organize_files_task_1
"""

    # List Tasks Parser
    list_parser = subparsers.add_parser("list", help="List all scheduled tasks", formatter_class=argparse.RawTextHelpFormatter)
    list_parser.epilog = """
Example usage:
    
    python task_manager.py list
"""

    # Start Scheduler Parser
    start_parser = subparsers.add_parser("start", help="Start the scheduler", formatter_class=argparse.RawTextHelpFormatter)
    start_parser.epilog = """
Example usage:
    
    *** 3 ways to start ***

    python task_manager.py start [press ctrl+c to stop]
    pythonw task_manager.py - For no terminal [Get-Process pythonw | Stop-Process -Force] (Windows)
    python task_manager.py [press ctrl+c to stop]
"""
    # Parse arguments
    args = parser.parse_args()

    # Create TaskManager object
    manager = TaskManager()

    # Handle commands
    if args.command == "add":
        manager.add_task(
            interval=args.interval,
            unit=args.unit,
            task_type=args.task_type,
            directory=args.directory,
            age_days=args.age_days,
            formats=args.formats,
            recipient_email=args.recipient_email,
            subject=args.subject,
            message=args.message,
            attachments=args.attachments,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            input_format=args.input_format,
            output_format=args.output_format,
            compression_format=args.compression_format,
        )
    elif args.command == "remove":
        manager.remove_task(args.task_name)
    elif args.command == "list":
        manager.list_tasks()
    elif args.command == "start":
        manager.start_scheduler()
    else:
        parser.print_help()

    # Start the scheduler thread only if no other command is given
    if not args.command:
        scheduler_thread = threading.Thread(target=manager.start_scheduler, daemon=True)
        scheduler_thread.start()
        print("Scheduler started in the background.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
            manager.scheduler.shutdown()

    