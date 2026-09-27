# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Install packages
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Start the server
python manage.py runserver

Listed directory yajmaan
Viewed requirements.txt:1-12
Viewed .env.example:1-24
Listed directory apps
Listed directory yajaman
Listed directory yajmaan
Ran command: `python --version`
Ran command: `py --version`
Viewed .env:1-21
Viewed urls.py:1-27

To run the **Yajmaan** Django REST Framework application, follow these step-by-step instructions in your terminal (PowerShell or Command Prompt):

---

### Prerequisites
Make sure **Python 3.10+** is installed on your machine and added to your system `PATH`. You can verify this by running:
```powershell
python --version
```
*(If Python is not installed, download and install it from [python.org](https://www.python.org/) and check the box to **"Add Python to PATH"** during installation).*

---

### Step 1: Navigate to the Project Directory
Make sure your terminal is inside the project root:
```powershell
cd c:\Users\rahul\OneDrive\Desktop\Projects\yajmaan\yajmaan
```

---

### Step 2: Create & Activate a Virtual Environment
It is recommended to use a virtual environment to manage dependencies.

1. **Create the environment:**
   ```powershell
   python -m venv venv
   ```

2. **Activate the environment:**
   - **PowerShell:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(If script execution is restricted in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*
   - **Command Prompt (cmd):**
     ```cmd
     venv\Scripts\activate.bat
     ```

---

### Step 3: Install Required Dependencies
Install the required packages listed in [requirements.txt](file:///c:/Users/rahul/OneDrive/Desktop/Projects/yajmaan/yajmaan/requirements.txt):
```powershell
pip install -r requirements.txt
```

---

### Step 4: Verify Environment Configuration (`.env`)
The project contains a [.env](file:///c:/Users/rahul/OneDrive/Desktop/Projects/yajmaan/yajmaan/.env) file. 

- **Using Supabase / Cloud PostgreSQL:** By default, [.env](file:///c:/Users/rahul/OneDrive/Desktop/Projects/yajmaan/yajmaan/.env) is configured with a Supabase PostgreSQL connection string (`DATABASE_URL`).
- **Using Local SQLite (Alternative):** If you prefer running locally without internet/Supabase, change line 7 in [.env](file:///c:/Users/rahul/OneDrive/Desktop/Projects/yajmaan/yajmaan/.env) to:
  ```ini
  DATABASE_URL=sqlite:///db.sqlite3
  ```

---

### Step 5: Run Database Migrations
Apply database migrations to set up the schema tables:
```powershell
python manage.py migrate
```

*(Optional)* Create an admin account to log into the Django Admin dashboard:
```powershell
python manage.py createsuperuser
```

---

### Step 6: Start the Development Server
Launch the Django server:
```powershell
python manage.py runserver
```

The server will start running locally at **`http://127.0.0.1:8000/`**.

---

### Useful URLs & API Documentation

Once the server is running, open your browser to access:

| Endpoint | Description | URL |
| :--- | :--- | :--- |
| 🚀 **Swagger API Docs** | Interactive OpenAPI testing console | [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) |
| 📖 **ReDoc** | Clean API reference documentation | [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/) |
| 🔐 **Django Admin** | Superuser database management panel | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |
| 🏠 **Home Feed API** | Application Home Feed endpoint | `http://127.0.0.1:8000/api/v1/home/` |