# Employee Management System — SE PBL

A responsive web app built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features
- Separate Admin and Employee login options
- Midnight-black sparkle theme with responsive laptop/mobile layout
- Employees can mark only their own attendance (Present, Late, or Leave)
- Admin attendance page is read-only; admin cannot edit attendance
- Employees can submit and track their own leave requests; admin can approve/reject
- Demo admin login
- Dashboard summary
- Employee create, read, update and delete (CRUD)
- Employee search
- Daily attendance records
- Leave request creation and approve/reject
- Monthly salary overview
- Responsive layout for laptop and mobile browsers
- SQLite database created automatically on first run with sample employees

## Requirements
- Python 3.11 or newer
- VS Code (recommended) with the Microsoft Python extension

## Windows setup
1. Install Python from https://www.python.org/downloads/ and tick **Add Python to PATH** during installation.
2. Open this project folder in VS Code.
3. Open **Terminal → New Terminal** and run:

   ```powershell
   py -m venv .venv
   .venv\\Scripts\\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run `.venv\\Scripts\\activate.bat`, then install requirements and start the app.
4. Open http://127.0.0.1:5000 in your laptop browser.

## Demo logins
- **Admin:** username `admin`, password `admin123`
- **Employee:** email `aman@example.com`, password `employee123`
- Another sample employee: `priya@example.com`, password `employee123`

Employee login uses the employee email stored in the employee list. For this classroom demo, all sample employee accounts use the same demo password; use real password storage before real-world deployment.

## Open on a phone using the same Wi-Fi
1. Keep the app running on the laptop.
2. Find the laptop's local IPv4 address with `ipconfig` in Command Prompt.
3. On your phone, connected to the same trusted Wi-Fi, open `http://LAPTOP-IP:5000` (replace LAPTOP-IP with the laptop's IPv4 address).
4. If Windows Firewall asks, allow Python only on a trusted private network.

Do not expose this development server to the public internet. The demo login is hard-coded for classroom demonstration and is not suitable for real business use. Change the secret key and implement proper authentication before deployment. Back up `employees.db` before deleting or replacing the project.

## Database
The `employees.db` file is created automatically next to `app.py`. It contains employees, attendance and leave tables. Salary is stored as a monthly amount in the employee record; this demo does not process real payroll payments.


### Employee login accounts
When adding a new employee as admin, set an Employee Login ID and password (minimum 6 characters). The employee signs in using that Login ID and password. Passwords are stored as secure hashes. Existing demo accounts: `aman` / `employee123` and `priya` / `employee123`.
