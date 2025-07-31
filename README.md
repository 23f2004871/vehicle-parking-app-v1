#  Vehicle Parking App - V1

A full-stack, multi-user web application for managing and booking vehicle parking spots, built with **Flask**. This project includes a comprehensive **Admin Panel** for management and an interactive, **map-based dashboard** for users.

---

##  Features

###  User Features

- **Interactive Map Dashboard**  
  View and explore parking lots on an interactive map powered by Leaflet.js.

- **Advanced Search & Filtering**  
  Search for lots by name/address and filter by status (e.g., "Open Now").

- **Detailed Booking System**  
  Select a registered vehicle and choose the type of spot (Standard, Premium, or EV).

- **Reservation Lifecycle**  
  Book, check-in to start the timer, and release to end the session.

- **QR Code Generation**  
  Each successful booking generates a unique QR code.

- **Reviews and Ratings**  
  Leave reviews and star ratings after a parking session.

- **Payment System**  
  Mock payment workflow with a detailed receipt after releasing a spot.

- **Profile & Vehicle Management**  
  Manage your personal information, change passwords, and add/remove vehicles.

- **Email Notifications**  
  Automated emails for registration confirmations and successful bookings.

---

###  Admin Features

- **Summary Dashboard**  
  View total users, total revenue, and reservation trends (Chart.js).

- **Full Lot Management (CRUD)**  
  Create, read, update, and delete parking lots with attributes like location, price, levels, etc.

- **Visual Spot Map**  
  Real-time status of each parking spot (Available / Occupied) in a lot.

- **User Management**  
  Activate/deactivate user accounts and view user lists.

- **Data Export**  
  Export reservation and user data to CSV for reporting.

- **RESTful API**  
  Programmatic access to all data via Flask-RESTful.

---

##  Tech Stack

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-RESTful, Flask-Mail, Werkzeug  
- **Database**: SQLite  
- **Frontend**: HTML5, CSS3, Bootstrap 5, Jinja2  
- **JavaScript Libraries**: Leaflet.js, Chart.js  
- **Python Libraries**: `qrcode[pil]`

---

##  Project Structure

```
/
├── app.py              # Main application file
├── models/             # SQLAlchemy models
├── controllers/        # Blueprints: auth, admin, user, api
├── templates/          # HTML templates
├── static/             # CSS, JS, and QR code images
├── requirements.txt    # Python dependencies
└── README.md           # Project overview
```

---

##  Setup and Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <project-folder>
```

### 2. Create a Virtual Environment

**For Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**For macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Email (Optional)

If you want to test the email feature, update the email configuration variables in `app.py`:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

---

##  Running the Application

### 1. Start the Flask Server

```bash
python app.py
```

You should see the server running on `http://127.0.0.1:5000`.

### 2. First-Time Database Initialization

- Creates the SQLite DB file `v_database.db`
- Initializes required tables
- Seeds:
  - Default admin account
  - Sample parking lots (e.g., Chennai locations)

---

##  Access the Application

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

##  Default Admin Credentials

- **Username**: `admin@vparking.com`  
- **Password**: `admin@vehicle`

---

