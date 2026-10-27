# Online Job Portal - Full Stack Development (FSD) Project

A complete Full Stack Web Application built with **Flask (Python)**, **MySQL / SQLite**, and **HTML5/CSS3/JavaScript**.

---

## 🚀 How to Run the Project

### Step 1: Open Terminal in the Project Directory
```powershell
cd "c:\Laxmi Project\FSD Project"
```

### Step 2: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(Or in standard cmd: `.\.venv\Scripts\activate.bat`)*

### Step 3: Verify Connection
```powershell
python test_connection.py
```

### Step 4: Start the Flask Backend Server
```powershell
python app.py
```

### Step 5: Open in Your Web Browser
Go to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Demo Login Accounts

The database comes pre-seeded with two accounts and 4 active job listings:

| Role | Email | Password |
|---|---|---|
| **Employer** | `employer@example.com` | `password123` |
| **Job Seeker** | `seeker@example.com` | `password123` |

*(You can also register your own new employer or job seeker account from the **Register** page!)*

---

## 🗄️ Database Configuration

This project supports **both MySQL and SQLite**:

### Option A: Using SQLite (Default / Plug-and-Play)
- Works out of the box without installing or running any database server.
- The SQLite database file `online_job_portal.db` is already created and ready.

### Option B: Using MySQL (e.g., via XAMPP)
1. Start **Apache** and **MySQL** in your **XAMPP Control Panel**.
2. Open [`.env`](file:///c:/Laxmi%20Project/FSD%20Project/.env) and configure your MySQL credentials:
   ```env
   DB_ENGINE=mysql
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=online_job_portal
   ```
   *(If you are using default XAMPP, `DB_PASSWORD` is usually empty: `DB_PASSWORD=`)*
3. Run the database initializer to automatically create the database and tables:
   ```powershell
   python init_db.py --mysql
   ```

---

## 📂 Project Architecture

```
FSD Project/
├── app.py                # Flask Backend (Routing, Authentication, Controllers)
├── db.py                 # Database Connection Manager (MySQL + SQLite)
├── init_db.py            # Automated Database Initializer & Seeder
├── test_connection.py    # Health check & connection diagnostic script
├── schema.sql            # MySQL Database schema definitions
├── .env                  # Configuration variables (DB credentials, SECRET_KEY)
├── requirements.txt      # Python dependencies
├── static/
│   ├── style.css         # Modern, responsive styling
│   └── script.js         # Frontend interactive behavior
└── templates/
    ├── base.html         # Base layout template with dynamic navigation
    ├── index.html        # Landing / Home page
    ├── jobs.html         # Job search & listings
    ├── job_details.html  # Job view & application submission
    ├── login.html        # User login
    ├── register.html     # User registration (Job Seeker / Employer)
    ├── post_job.html     # Employer job posting
    ├── employer_dashboard.html   # Employer dashboard & applicant management
    └── jobseeker_dashboard.html  # Job seeker dashboard & status tracker
```

---

## ⚡ Deploy to Vercel

This project includes ready-to-deploy Vercel configuration (`vercel.json` and `api/index.py`):

1. Push your code to GitHub:
   ```powershell
   git add .
   git commit -m "Configure Vercel deployment"
   git push
   ```
2. Go to **[vercel.com](https://vercel.com/)** and sign in with GitHub.
3. Click **Add New...** → **Project**, and select your repository.
4. Leave Framework Preset as **Other** and click **Deploy**.
5. Your project will be live with a free `https://<your-project>.vercel.app` URL!
