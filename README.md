# **AutoPyGo: Automated Task Management 🚀**  

AutoPyGo is a versatile application that combines **Python** and **Go** tools to automate tasks, fetch logs, and provide a user-friendly **web-based task scheduler**.  

## **Overview**  

### ✨ Features  
- **Python CLI (Task Manager):** Automate tasks like file organization, email sending, and more via the command line.  
- **Go CLI (Log Fetcher):** Efficiently retrieve logs using a fast Go-based tool.  
- **Web Dashboard:** Schedule, monitor, and manage automated tasks through an intuitive web interface.  
- **Task Logging:** Track execution history.  
- **Flexible File Handling:** Process CSV, Excel, and text files.  

---

## **Getting Started**  

### **1️⃣ Clone the Repository**  
```bash
git clone <repository-url>
cd autopygo
```
### **2️⃣ Set Up Python Environment**  
Follow these steps to set up the Python virtual environment and install dependencies:  

1. **Create a Virtual Environment:**  
   ```bash
   python -m venv venv
2. **Activate the Virtual Environment:**
   
   For macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   For Windows:
   ```
   venv\Scripts\activate
   ```
3. **Install Required Dependencies:**
   ```
   pip install -r python_cli/requirements.txt
   ```
### **3️⃣ Set Up MongoDB**  
Ensure that **MongoDB** is installed and running. If MongoDB is not installed, follow these steps:

#### **1. Install MongoDB**
##### **For Ubuntu/Debian:**  
Run the following commands to install MongoDB on a Linux system:  
```bash
  sudo apt update
  sudo apt install -y mongodb
```
#### **For Windows:**  
1. Download the **MongoDB Community Server** from [MongoDB's official website](https://www.mongodb.com/try/download/community).  
2. Follow the installation instructions provided in the setup wizard.  
3. Ensure that **MongoDB** is configured to run as a service during installation.  
4. Once installed, open **Services** (`Win + R`, type `services.msc`, and press **Enter**).  
5. Locate **MongoDB Server**, right-click, and click **Start** to run MongoDB.  

#### **For macOS (Using Homebrew):**

```
  brew tap mongodb/brew
  brew install mongodb-community@6.0
```
#### **2. Start MongoDB Service**

Once MongoDB is installed, start the service:

**For Linux/macOS:**
```
  sudo systemctl start mongodb

```
To verify that MongoDB is running:

```
  sudo systemctl status mongodb

```
To enable MongoDB to start on boot:

```
  sudo systemctl enable mongodb

```
#### **3. Verify MongoDB Installation**

To confirm that MongoDB is running, use the following command:

```
mongo --eval "db.runCommand({ connectionStatus: 1 })"
```
If MongoDB is correctly set up, you should see a response indicating "ok": 1.

#### **4. Create a Database and Collection**
Once MongoDB is running, create the necessary database and collection:

**1. Open the MongoDB Shell:**

```
mongo

```
**2. Create and use the database:**
```
use task_manager_db

```
**3. Create a collection for logs:**
```
db.createCollection("logs")

```
**4. Exit the MongoDB shell:**

```
exit
```
#### **5. Configure MongoDB for AutoPyGo**
Ensure the MongoDB connection details are set in the .env file inside both python_cli and go_cli folders:

Create a `.env` file inside the `python_cli` and `go_cli` folders with the following configuration details:  

```ini
# Python CLI
SENDER_EMAIL=dummyemail@example.com  
SENDER_PASSWORD=dummypassword123  

# Go & Python CLI
MONGO_URI=mongodb://localhost:27017/  
DB_NAME=task_manager_db  
COLLECTION_NAME=logs  
```

### **4️⃣ Build Go CLI**  
Follow these steps to set up and build the Go CLI:  

1. **Navigate to the `go_cli` Directory:**  
```bash
cd go_cli
```
2. **Initialize the Go Module:**
```
go mod init go_cli
```
3. **Tidy Up Dependencies:**
```
go mod tidy
```
### **5️⃣ Run the Application**  
Once the setup is complete, you can start the application using the following command:

**For Windows:**
```bash
python main_menu.py 
```
**For Linux:**
```bash
python3 main_menu.py 
```
This will launch the main menu, where you can choose from different options:

### **How to Use**
Main Menu Options

1️⃣ Launch Python CLI Task Manager

2️⃣ Launch Go CLI Log Fetcher

3️⃣ Start Web Dashboard (http://127.0.0.1:5000/)

4️⃣ Exit

Your application is now up and running! 🚀

## **Python CLI (Task Manager)**  
- Automate **file organization, email sending,** and other tasks.  
- Run the following command to see available commands:  

  ```bash
  python python_cli/task_manager.py --h

## **Go CLI (Log Fetcher)**  

- Fetch logs from a **MongoDB database** efficiently.  
- Run the following command to execute the log fetcher:  

  ```bash
  go run go_cli/main.go


## **Web Dashboard 🌐**  

### **How to Use**  
1. **Start the Web UI** (`Option 3` in the main menu).  
2. **Add Tasks:** Fill out the form on the **"Manage Tasks"** page.  
3. **Remove Tasks:** Delete unwanted scheduled tasks.  
4. **List Tasks:** View all scheduled tasks.  
5. **Upload Files:** Upload **CSV, Excel,** or **text files** for automation tasks.  


### Web Page Descriptions

* **home.html:** Provides an overview of available automated tasks.
* **index.html:** Enables adding, listing, and removing automated tasks.








