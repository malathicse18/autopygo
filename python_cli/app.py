# app.py
from flask import Flask, render_template, request, flash, jsonify, get_flashed_messages, redirect, url_for, session
from task_manager import TaskManager  # Ensure task_manager.py exists
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


@app.route("/", methods=["GET"])
def home():
    """Renders the home page."""
    return render_template("home.html")


@app.route("/index", methods=["GET", "POST"])
def index():
    """Handle the main page and task submission."""
    tasks = manager.load_tasks()  # Load tasks here for both GET and POST

    if request.method == "POST":
        try:
            task_type = request.form.get("task_type")
            interval = request.form.get("interval")
            unit = request.form.get("unit")

            if not interval or not interval.isdigit():
                flash("Invalid or missing interval!", "error")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"tasks": tasks, "messages": get_flash_messages()})
                else:
                    return render_template("index.html", tasks=tasks, messages=get_flash_messages())

            interval = int(interval)

            # Organize Files
            if task_type == "organize_files":
                directory = request.form.get("directory")
                if not directory:
                    flash("Directory is required for organizing files.", "error")
                elif manager.add_task(interval, unit, task_type, directory=directory):
                    flash("Task added successfully!", "success")
                else:
                    flash("Task already exists!", "error")

            # Delete Files
            elif task_type == "delete_files":
                directory = request.form.get("directory")
                age_days = request.form.get("age_days")
                formats = request.form.get("formats")

                if not directory or not age_days or not formats:
                    flash("Directory, age, and formats are required for deleting files.", "error")
                else:
                    age_days = int(age_days)
                    formats = formats.split(",")
                    if manager.add_task(interval, unit, task_type, directory=directory, age_days=age_days, formats=formats):
                        flash("Task added successfully!", "success")
                    else:
                        flash("Task already exists!", "error")

            # Send Email
            elif task_type == "send_email":
                recipient_file = request.files.get("recipient_file")
                recipient_emails = []

                if recipient_file:
                    try:
                        for line in recipient_file.readlines():
                            line = line.strip().decode("utf-8")
                            recipient_emails.append(line)
                    except Exception as e:
                        flash(f"Error processing recipient file: {e}", "error")
                else:
                    recipient_email = request.form.get("recipient_email")
                    if recipient_email:
                        recipient_emails = [recipient_email.strip()]

                subject = request.form.get("subject")
                if not subject:
                    flash("Subject is required for sending emails.", "error")

                message_file = request.files.get("message_file")
                message = ""
                if message_file:
                    try:
                        message = message_file.read().decode("utf-8")
                    except UnicodeDecodeError:
                        flash("Unable to decode message file. Check encoding.", "error")
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
                            flash(f"Failed to save attachment: {e}", "error")

                if manager.add_task(interval, unit, task_type, recipient_email=recipient_emails, subject=subject, message=message, attachments=attachment_paths):
                    flash("Task added successfully!", "success")
                else:
                    flash("Task already exists!", "error")

            # Get Gold Rate
            elif task_type == "get_gold_rate":
                if manager.add_task(interval, unit, task_type):
                    flash("Task added successfully!", "success")
                else:
                    flash("Task already exists!", "error")

            # Convert File
            elif task_type == "convert_file":
                input_dir = request.form.get("input_dir")
                output_dir = request.form.get("output_dir")
                input_format = request.form.get("input_format")
                output_format = request.form.get("output_format")

                if not input_dir or not output_dir or not input_format or not output_format:
                    flash("All fields are required for file conversion.", "error")
                elif manager.add_task(interval, unit, task_type, input_dir=input_dir, output_dir=output_dir, input_format=input_format, output_format=output_format):
                    flash("Task added successfully!", "success")
                else:
                    flash("Task already exists!", "error")

            # Compress Files
            elif task_type == "compress_files":
                directory = request.form.get("directory")
                output_dir = request.form.get("output_dir")
                compression_format = request.form.get("compression_format")

                if not directory or not output_dir or not compression_format:
                    flash("All fields are required for file compression.", "error")
                elif manager.add_task(interval, unit, task_type, directory=directory, output_dir=output_dir, compression_format=compression_format):
                    flash("Task added successfully!", "success")
                else:
                    flash("Task already exists!", "error")

            tasks = manager.load_tasks()  # Reload tasks after adding
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"tasks": tasks, "messages": get_flash_messages()})
            else:
                return render_template("index.html", tasks=tasks, messages=get_flash_messages())

        except Exception as e:
            logger.error(f"Error adding task: {e}")
            flash(f"Error adding task: {e}", "error")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"tasks": tasks, "messages": get_flash_messages()})
            else:
                return render_template("index.html", tasks=tasks, messages=get_flash_messages())

    messages = get_flash_messages()
    return render_template("index.html", tasks=tasks, messages=messages)


@app.route("/remove_task/", defaults={"task_name": None}, methods=["POST"])
@app.route("/remove_task/<task_name>", methods=["POST"])
def remove_task(task_name):
    """Remove a task by its name."""
    try:
        if not task_name:
            task_name = request.form.get("task_name")
            if not task_name or not task_name.strip():
                flash("Task name is required!", "error")
                return jsonify({"tasks": manager.load_tasks(), "messages": get_flash_messages()})

        # Clear existing flash messages
        session.pop('_flashes', None)

        # task_removed = manager.remove_task(task_name.strip())  # Capture the return value
        if task_name:
            if task_name not in manager.load_tasks():
                flash("Task not found!", "error")
                return redirect(url_for('index'))
            task_removed = manager.remove_task(task_name.strip())  # Capture the return value
            flash("Task removed successfully!", "success")
            return redirect(url_for('index'))

        # if task_removed:
        #     flash("Task removed successfully!", "success")
        # else:
        #     flash("Task not found!", "error")

    except Exception as e:
        logger.error(f"Error removing task: {e}")
        flash(f"Error removing task: {e}", "error")

    tasks = manager.load_tasks()  # Reload tasks after removing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = jsonify({"tasks": tasks, "messages": get_flash_messages()})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        return redirect(url_for('index'))


def get_flash_messages():
    """Get flashed messages and format them for JSON response."""
    return [{"category": category, "message": message} for category, message in get_flashed_messages(with_categories=True)]


if __name__ == "__main__":
     app.run(debug=True, host='0.0.0.0')  # Enable debug mode for development