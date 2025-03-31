import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import json
import pandas as pd
import smtplib
import task_manager  # Import your task_manager module
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.jobstores.base import JobStore
import requests
from docx import Document
from fpdf import FPDF
import zipfile
import tarfile

class MockJobStore(JobStoreBase):
    """A simple mock job store for testing."""

    def __init__(self):
        super().__init__()
        self.jobs = {}

    def add_job(self, job):
        self.jobs[job.id] = job

    def remove_job(self, job_id):
        if job_id in self.jobs:
            del self.jobs[job_id]

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def get_all_jobs(self):
        return list(self.jobs.values())

    def remove_all_jobs(self):
        self.jobs.clear()

class TestTaskManager(unittest.TestCase):

    def setUp(self):
        self.task_manager = task_manager.TaskManager()
        self.test_dir = "test_dir"
        self.output_dir = "output_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.tasks_file = "test_scheduled_tasks.json"
        self.task_manager.tasks_file = self.tasks_file
        self.task_manager.scheduler.remove_all_jobs()
        self.task_manager.scheduler.shutdown(wait=False)
        self.task_manager.scheduler = BaseScheduler()
        self.mock_job_store = MockJobStore()
        self.task_manager.scheduler.add_jobstore(self.mock_job_store, 'default')
        self.task_manager.scheduler.start()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)
        if os.path.exists(self.tasks_file):
            os.remove(self.tasks_file)
        self.task_manager.scheduler.remove_all_jobs()
        self.task_manager.scheduler.shutdown(wait=False)

    def create_test_file(self, filename, content="Test content"):
        with open(os.path.join(self.test_dir, filename), "w") as f:
            f.write(content)

    @patch("task_manager.MongoClient")
    def test_log_to_mongodb(self, mock_mongo_client):
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo_client.return_value.__getitem__.return_value = mock_db

        self.task_manager.log_to_mongodb("test_task", "test details", "success")
        mock_collection.insert_one.assert_called_once()

    def test_load_tasks(self):
        tasks = {"task1": {"interval": 1, "unit": "days", "task_type": "organize_files", "directory": "test"}}
        with open(self.tasks_file, "w") as f:
            json.dump(tasks, f)
        self.assertEqual(self.task_manager.load_tasks(), tasks)

        os.remove(self.tasks_file)
        self.assertEqual(self.task_manager.load_tasks(), {})

        with open(self.tasks_file, "w") as f:
            f.write("invalid json")
        self.assertEqual(self.task_manager.load_tasks(), {})

    def test_save_tasks(self):
        tasks = {"task1": {"interval": 1, "unit": "days", "task_type": "organize_files", "directory": "test"}}
        self.task_manager.save_tasks(tasks)
        with open(self.tasks_file, "r") as f:
            self.assertEqual(json.load(f), tasks)

    def test_organize_files(self):
        self.create_test_file("test1.txt")
        self.create_test_file("test2.jpg")
        self.task_manager.organize_files(self.test_dir)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Documents", "test1.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Images", "test2.jpg")))

        self.task_manager.organize_files(self.test_dir) #test when no files

        with patch("os.listdir", side_effect=OSError("Test error")):
            self.task_manager.organize_files(self.test_dir)

    def test_delete_files(self):
        self.create_test_file("old_file.txt")
        old_file_path = os.path.join(self.test_dir, "old_file.txt")
        os.utime(old_file_path, (1, 1))
        self.task_manager.delete_files(self.test_dir, 1, [".txt"])
        self.assertFalse(os.path.exists(old_file_path))

        self.task_manager.delete_files(self.test_dir, 1, [".txt"]) #test no files.

        with patch("os.walk", side_effect=OSError("Test error")):
            self.task_manager.delete_files(self.test_dir, 1, [".txt"])

    @patch("os.getenv")
    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp, mock_getenv):
        mock_getenv.side_effect = ["test@example.com", "password"]
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        self.assertTrue(self.task_manager.send_email("recipient@example.com", "Test Subject", "Test Message"))

        mock_getenv.return_value = None
        self.assertFalse(self.task_manager.send_email("recipient@example.com", "Test Subject", "Test Message"))

        mock_smtp.side_effect = smtplib.SMTPException("SMTP error")
        self.assertFalse(self.task_manager.send_email("recipient@example.com", "Test Subject", "Test Message"))

    def test_is_valid_email(self):
        self.assertTrue(self.task_manager.is_valid_email("test@example.com"))
        self.assertFalse(self.task_manager.is_valid_email("invalid-email"))

    @patch("requests.get")
    @patch("pandas.DataFrame.to_excel")
    def test_get_gold_rate(self, mock_to_excel, mock_requests_get):
        mock_response = MagicMock()
        mock_response.text = '<html><body><span class="white-space-nowrap">50000</span></body></html>'
        mock_requests_get.return_value = mock_response
        self.assertEqual(self.task_manager.get_gold_rate(), "50000")

        mock_requests_get.side_effect = requests.exceptions.RequestException("Request error")
        self.assertIsNone(self.task_manager.get_gold_rate())

        mock_response.text = '<html><body><span>No price here</span></body></html>'
        self.assertIsNone(self.task_manager.get_gold_rate())

    def test_convert_file(self):
        self.create_test_file("test.txt", "hello world")
        self.task_manager.convert_file(self.test_dir, self.output_dir, "txt", "csv")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test.csv")))

        self.create_test_file("test.txt", "hello world")
        self.task_manager.convert_file(self.test_dir, self.output_dir, "txt", "pdf")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test.pdf")))
        self.create_test_file("test.csv", "col1,col2\na,b")
        self.task_manager.convert_file(self.test_dir, self.output_dir, "csv", "xlsx")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test.xlsx")))

        try:
            doc = Document()
            doc.add_paragraph("Hello World")
            doc_path = os.path.join(self.test_dir, "test.docx")
            doc.save(doc_path)
            self.task_manager.convert_file(self.test_dir, self.output_dir, "docx", "pdf")
            self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test.pdf")))
        except ImportError:
            pass #Skip if docx module not installed

        with self.assertRaises(ValueError):
            self.task_manager.convert_file(self.test_dir, self.output_dir, "abc", "xyz")

        with patch("os.listdir", side_effect=OSError("Test error")):
            self.task_manager.convert_file(self.test_dir, self.output_dir, "txt", "csv")

    def test_compress_files(self):
        self.create_test_file("test1.txt")
        self.task_manager.compress_files(self.test_dir, self.output_dir, "zip")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test_dir.zip")))

        self.create_test_file("test1.txt")
        self.task_manager.compress_files(self.test_dir, self.output_dir, "tar")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "test_dir.tar")))

        with self.assertRaises(ValueError):
            self.task_manager.compress_files(self.test_dir, self.output_dir, "rar")

        with patch("os.makedirs", side_effect=OSError("Test error")):
            self.task_manager.compress_files(self.test_dir, self.output_dir, "zip")

    def test_add_task(self):
        self.assertTrue(self.task_manager.add_task(1, "days", "organize_files", directory=self.test_dir))
        tasks = self.task_manager.load_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(list(tasks.values())[0]["task_type"], "organize_files")

        self.assertTrue(self.task_manager.add_task(1, "days", "delete_files", directory=self.test_dir, age_days=30, formats=[".txt"]))
        self.assertTrue(self.task_manager.add_task(1, "days", "send_email", recipient_email="test@example.com", subject="Test", message="Test"))
        self.assertTrue(self.task_manager.add_task(1, "hours", "get_gold_rate"))
        self.assertTrue(self.task_manager.add_task(1, "days", "convert_file", input_dir=self.test_dir, output_dir=self.output_dir, input_format="txt", output_format="csv"))
        self.assertTrue(self.task_manager.add_task(1, "days", "compress_files", directory=self.test_dir, output_dir=self.output_dir, compression_format="zip"))

        with self.assertRaises(ValueError):
            self.task_manager.add_task(1, "days", "invalid_task")

        #test duplicate task detection.
        self.assertFalse(self.task_manager.add_task(1, "days", "organize_files", directory=self.test_dir))
        self.assertFalse(self.task_manager.add_task(1, "days", "delete_files", directory=self.test_dir, age_days=30, formats=[".txt"]))
        self.assertFalse(self.task_manager.add_task(1, "days", "send_email", recipient_email="test@example.com", subject="Test", message="Test"))
        self.assertFalse(self.task_manager.add_task(1, "hours", "get_gold_rate"))
        self.assertFalse(self.task_manager.add_task(1, "days", "convert_file", input_dir=self.test_dir, output_dir=self.output_dir, input_format="txt", output_format="csv"))
        self.assertFalse(self.task_manager.add_task(1, "days", "compress_files", directory=self.test_dir, output_dir=self.output_dir, compression_format="zip"))

    def test_remove_task(self):
        self.task_manager.add_task(1, "days", "organize_files", directory=self.test_dir)
        task_name = list(self.task_manager.load_tasks().keys())[0]

        self.assertTrue(self.task_manager.remove_task(task_name))
        self.assertEqual(len(self.task_manager.load_tasks()), 0)
        self.assertFalse(self.task_manager.remove_task("nonexistent_task"))

        #test job store removal.
        self.task_manager.add_task(1, "days", "organize_files", directory=self.test_dir)
        task_name2 = list(self.task_manager.load_tasks().keys())[0]
        with patch.object(self.task_manager.scheduler, 'get_job', return_value = self.task_manager.scheduler.get_job(task_name2)):
            self.assertTrue(self.task_manager.remove_task(task_name2))

    def test_list_tasks(self):
        self.task_manager.add_task(1, "days", "organize_files", directory=self.test_dir)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.task_manager.list_tasks()
            self.assertIn("organize_files", mock_stdout.getvalue())

        self.task_manager.remove_task(list(self.task_manager.load_tasks().keys())[0])
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.task_manager.list_tasks()
            self.assertIn("No tasks scheduled.", mock_stdout.getvalue())

    def test_load_and_schedule_tasks(self):
        tasks = {"task1": {"interval": 1, "unit": "days", "task_type": "organize_files", "directory": self.test_dir}}
        with open(self.tasks_file, "w") as f:
            json.dump(tasks, f)
        self.task_manager.load_and_schedule_tasks()
        self.assertEqual(len(self.task_manager.scheduler.get_jobs()), 1)

    def test_start_scheduler(self):
        with patch('time.sleep', side_effect=KeyboardInterrupt):
            self.task_manager.start_scheduler()