🎓 Placement Portal Web Application

A full-stack Placement Management System built using Flask (Python) and SQLite, designed to streamline campus recruitment by connecting Students, Companies, and Admin in a single platform.

🚀 Features
👨‍💼 Admin
Approve / Reject company registrations
Approve / Reject placement drives
Mark drives as completed
View all students and applications
Block / Unblock users
Monitor complete system activity
🏢 Company
Register and wait for admin approval
Create placement drives
Edit / Delete drives
View student applications
Accept / Reject candidates with remarks
🎓 Student
Register and login
Upload resume
Apply for placement drives
Track application status
View application history
Edit profile
🛠️ Tech Stack
Backend: Python (Flask)
Database: SQLite
Frontend: HTML, CSS (Jinja Templates)
Authentication: Session-based login system
File Handling: Resume upload system
📂 Project Structure
📦 Placement-Portal
 ┣ 📜 app.py
 ┣ 📜 database_helper.py
 ┣ 📜 placement.db
 ┣ 📂 templates/
 ┣ 📂 static/
 ┃ ┗ 📂 resumes/
 ┗ 📜 README.md
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/placement-portal.git
cd placement-portal
2️⃣ Install dependencies
pip install flask
3️⃣ Run the application
python app.py
4️⃣ Open in browser
http://127.0.0.1:5000/


Password is securely hashed using SHA-256.

🗄️ Database Design

The system uses SQLite with the following tables:

users → stores login credentials & roles
companies → company details & approval status
students → student profiles & resumes
drives → placement drives
applications → job applications

Database is automatically initialized using:

initialize_database()

🔌 API Endpoints

Basic REST APIs are defined for system interaction:

POST /login → User authentication
POST /register → User registration
POST /company/add_drive → Add placement drive
POST /student/apply → Apply for drive
GET /applications → View applications
POST /admin/approve_company → Approve company

📄 Full API documentation:

🔒 Security Features
Password hashing using SHA-256
Session-based authentication
Duplicate application prevention
Deadline validation for job applications
Admin-controlled access (block/unblock users)
💡 Key Functional Highlights
Prevents duplicate job applications
Handles resume uploads with unique filenames
Tracks application history with status & remarks
Ensures company and drive approval workflow
Implements role-based dashboards
🧪 Future Enhancements
Email notifications 📧
AI-based resume screening 🤖
Real-time chat between students & recruiters 💬
Advanced analytics dashboard 📊
Deployment on cloud (AWS / Heroku) ☁️

Author
Sarvesh Choudhary
Roll No: 23f1000300
📧 23f100300@ds.study.iitm.ac.in

📄 License
This project was developed as part of an academic submission at IIT Madras. All rights reserved.
