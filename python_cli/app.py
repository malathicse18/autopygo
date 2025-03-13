from flask import Flask, render_template, request, redirect, url_for, flash
from task_manager import TaskManager  # Assuming you have task_manager.py
import os
import threading
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for flashing messages

# Initialize TaskManager
manager = TaskManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the upload directory for attachments
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def start_scheduler():
    """Start the task scheduler in a separate thread."""
    manager.start_scheduler()

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle the main page and task submission."""
    if request.method == "POST":
        try:
            task_name = request.form.get("task_name")  # Ensure task_name is included in the form
            task_type = request.form.get("task_type")
            interval = int(request.form.get("interval"))
            unit = request.form.get("unit")

            # Check if the task already exists
            if manager.task_exists(task_name):
                flash(f"Task '{task_name}' already exists!", "error")
                return redirect(url_for("index"))

            if task_type == "organize_files":
                directory = request.form.get("directory")
                if not directory:
                    flash("Directory is required for organizing files.", "error")
                    return redirect(url_for("index"))
                manager.add_task(task_name, interval, unit, task_type, directory=directory)

            elif task_type == "delete_files":
                directory = request.form.get("directory")
                age_days = int(request.form.get("age_days"))
                formats = request.form.get("formats").split(",")
                if not directory or not formats:
                    flash("Directory and formats are required for deleting files.", "error")
                    return redirect(url_for("index"))
                manager.add_task(task_name, interval, unit, task_type, directory=directory, age_days=age_days, formats=formats)

            elif task_type == "send_email":
                recipient_file = request.files.get("recipient_file")
                recipient_emails = []

                if recipient_file:
                    # Read the file and extract email addresses
                    for line in recipient_file.readlines():
                        line = line.strip().decode('utf-8')
                        if "," in line:
                            _, email = line.split(",", 1)
                            recipient_emails.append(email.strip())
                        else:
                            recipient_emails.append(line.strip())
                else:
                    recipient_email = request.form.get("recipient_email")
                    if recipient_email:
                        recipient_emails = [recipient_email.strip()]

                subject = request.form.get("subject")
                if not subject:
                    flash("Subject is required for sending emails.", "error")
                    return redirect(url_for("index"))

                message_file = request.files.get("message_file")
                message = ""
                if message_file:
                    message_bytes = message_file.read()
                    if message_bytes:
                        try:
                            message = message_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            message = message_bytes.decode('latin-1', errors='replace')
                else:
                    message = request.form.get("message")

                attachments = request.files.getlist("attachments")
                attachment_paths = []

                for attachment in attachments:
                    if attachment.filename:
                        try:
                            filename = secure_filename(attachment.filename)
                            filepath = os.path.join(UPLOAD_DIR, filename)
                            attachment.save(filepath)
                            attachment_paths.append(filepath)
                        except Exception as e:
                            logger.error(f"Failed to save attachment: {e}")
                            flash(f"Failed to save attachment: {e}", "error")

                manager.add_task(
                    task_name,
                    interval,
                    unit,
                    task_type,
                    recipient_email=recipient_emails,
                    subject=subject,
                    message=message,
                    attachments=attachment_paths,
                )

            elif task_type == "get_gold_rate":
                manager.add_task(task_name, interval, unit, task_type)

            elif task_type == "convert_file":
                input_dir = request.form.get("input_dir")
                output_dir = request.form.get("output_dir")
                input_format = request.form.get("input_format")
                output_format = request.form.get("output_format")
                if not input_dir or not output_dir or not input_format or not output_format:
                    flash("All fields are required for file conversion.", "error")
                    return redirect(url_for("index"))
                manager.add_task(
                    task_name,
                    interval,
                    unit,
                    task_type,
                    input_dir=input_dir,
                    output_dir=output_dir,
                    input_format=input_format,
                    output_format=output_format,
                )

            elif task_type == "compress_files":
                directory = request.form.get("directory")
                output_dir = request.form.get("output_dir")
                compression_format = request.form.get("compression_format")
                if not directory or not output_dir or not compression_format:
                    flash("All fields are required for file compression.", "error")
                    return redirect(url_for("index"))
                manager.add_task(
                    task_name,
                    interval,
                    unit,
                    task_type,
                    directory=directory,
                    output_dir=output_dir,
                    compression_format=compression_format,
                )

            flash("Task added successfully!", "success")
            return redirect(url_for("index"))

        except Exception as e:
            logger.error(f"Error adding task: {e}")
            flash(f"Error adding task: {e}", "error")
            return redirect(url_for("index"))

    tasks = manager.load_tasks()
    return render_template("index.html", tasks=tasks)

@app.route("/remove_task/", methods=["GET"])
def remove_task():
    """Remove a task by its name."""
    task_name = request.args.get("task_name")
    if task_name:
        try:
            manager.remove_task(task_name)
            flash("Task removed successfully!", "success")
        except Exception as e:
            logger.error(f"Error removing task: {e}")
            flash(f"Error removing task: {e}", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for development