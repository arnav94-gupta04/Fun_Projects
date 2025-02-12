import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime, date

###########################################
# Database Setup and Models
###########################################

# Create an SQLite engine. For production, you may want to use PostgreSQL/MySQL.
engine = create_engine("sqlite:///erp.db", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# User table – note that we add a password_hash field for authentication.
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    aadhar_number = Column(String, unique=True, nullable=False)
    service_domain = Column(String)
    role = Column(String, nullable=False)  # 'admin', 'manager', 'staff', or 'client'
    level_of_employment = Column(String)
    date_of_joining = Column(Date)
    salary = Column(Float)
    certifications = Column(Text)
    password_hash = Column(String, nullable=False)

# Attendance table.
class Attendance(Base):
    __tablename__ = 'attendance'
    attendance_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    date = Column(Date, default=date.today())
    check_in = Column(Time)
    check_out = Column(Time)

# Service Tickets table.
class ServiceTicket(Base):
    __tablename__ = 'service_tickets'
    ticket_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False)
    service_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    assigned_to = Column(Integer)  # Assigned staff user ID (if any)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create the database tables.
Base.metadata.create_all(bind=engine)

###########################################
# Helper Functions
###########################################

def get_db():
    """Yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against the hashed version."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_user_by_email(db, email: str):
    """Retrieve a user by email."""
    return db.query(User).filter(User.email == email).first()

def create_user(db, user_data):
    """Create a new user record in the database."""
    new_user = User(
        full_name = user_data["full_name"],
        phone_number = user_data["phone_number"],
        email = user_data["email"],
        aadhar_number = user_data["aadhar_number"],
        service_domain = user_data.get("service_domain", ""),
        role = user_data["role"],
        level_of_employment = user_data.get("level_of_employment", ""),
        date_of_joining = user_data.get("date_of_joining", date.today()),
        salary = user_data.get("salary", 0.0),
        certifications = user_data.get("certifications", ""),
        password_hash = hash_password(user_data["password"])
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db, email: str, password: str):
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None

###########################################
# Session State Initialization
###########################################

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.experimental_rerun()

###########################################
# Login Page
###########################################

def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        db = next(get_db())
        user = authenticate_user(db, email, password)
        if user:
            st.success("Logged in successfully!")
            st.session_state.logged_in = True
            st.session_state.user = {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "role": user.role
            }
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

###########################################
# Admin: Register New User
###########################################

def register_user():
    st.header("Register New User")
    full_name = st.text_input("Full Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email")
    aadhar_number = st.text_input("Aadhar Card Number")
    service_domain = st.text_input("Service Domain")
    role = st.selectbox("Role", ["staff", "client", "manager", "admin"])
    level_of_employment = st.text_input("Level of Employment")
    date_of_joining = st.date_input("Date of Joining", date.today())
    salary = st.number_input("Salary", value=0.0)
    certifications = st.text_area("Certifications")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        else:
            db = next(get_db())
            if get_user_by_email(db, email):
                st.error("A user with this email already exists!")
            else:
                user_data = {
                    "full_name": full_name,
                    "phone_number": phone_number,
                    "email": email,
                    "aadhar_number": aadhar_number,
                    "service_domain": service_domain,
                    "role": role,
                    "level_of_employment": level_of_employment,
                    "date_of_joining": date_of_joining,
                    "salary": salary,
                    "certifications": certifications,
                    "password": password
                }
                create_user(db, user_data)
                st.success("User registered successfully!")

###########################################
# Staff: Attendance Module
###########################################

def staff_attendance():
    st.header("Attendance")
    db = next(get_db())
    today = date.today()
    user_id = st.session_state.user["user_id"]
    # Look for an existing attendance record for today.
    attendance_record = db.query(Attendance).filter(Attendance.user_id == user_id, Attendance.date == today).first()
    
    if attendance_record is None:
        if st.button("Check In"):
            new_attendance = Attendance(
                user_id=user_id,
                date=today,
                check_in=datetime.now().time()
            )
            db.add(new_attendance)
            db.commit()
            st.success("Checked in successfully!")
            st.experimental_rerun()
    else:
        if attendance_record.check_out is None:
            st.write(f"Checked in at: {attendance_record.check_in}")
            if st.button("Check Out"):
                attendance_record.check_out = datetime.now().time()
                db.commit()
                st.success("Checked out successfully!")
                st.experimental_rerun()
        else:
            st.write("You have already checked in and out for today.")
            st.write(f"Check In: {attendance_record.check_in} | Check Out: {attendance_record.check_out}")

###########################################
# Client: Service Request Module
###########################################

def client_service_request():
    st.header("Raise Service Request")
    service_type = st.selectbox("Service Type", ["Housekeeping", "Pantry", "Car Driver", "Data Entry", "Electrician", "Plumber", "Gardener"])
    description = st.text_area("Description")
    if st.button("Submit Request"):
        db = next(get_db())
        new_ticket = ServiceTicket(
            client_id=st.session_state.user["user_id"],
            service_type=service_type,
            description=description,
            status="Pending"
        )
        db.add(new_ticket)
        db.commit()
        st.success("Service request submitted successfully!")

def client_view_tickets():
    st.header("My Service Tickets")
    db = next(get_db())
    tickets = db.query(ServiceTicket).filter(ServiceTicket.client_id == st.session_state.user["user_id"]).all()
    if tickets:
        for ticket in tickets:
            st.write(f"**Ticket ID:** {ticket.ticket_id}")
            st.write(f"**Service Type:** {ticket.service_type}")
            st.write(f"**Description:** {ticket.description}")
            st.write(f"**Status:** {ticket.status}")
            st.write("---")
    else:
        st.write("No service tickets found.")

###########################################
# Manager: Service Ticket Management
###########################################

def manager_service_tickets():
    st.header("Manage Service Tickets")
    db = next(get_db())
    tickets = db.query(ServiceTicket).all()
    if tickets:
        for ticket in tickets:
            st.write(f"**Ticket ID:** {ticket.ticket_id}")
            st.write(f"**Client ID:** {ticket.client_id}")
            st.write(f"**Service Type:** {ticket.service_type}")
            st.write(f"**Description:** {ticket.description}")
            st.write(f"**Status:** {ticket.status}")
            # If the ticket is still pending, allow assignment.
            if ticket.status == "Pending":
                staff_list = db.query(User).filter(User.role=="staff").all()
                staff_options = {f"{s.full_name} (ID: {s.user_id})": s.user_id for s in staff_list}
                # Using a unique key for each selectbox.
                selected_staff = st.selectbox(f"Assign Ticket {ticket.ticket_id} to:", options=list(staff_options.keys()), key=f"ticket_{ticket.ticket_id}")
                if st.button(f"Assign Ticket {ticket.ticket_id}", key=f"assign_{ticket.ticket_id}"):
                    ticket.assigned_to = staff_options[selected_staff]
                    ticket.status = "In Progress"
                    db.commit()
                    st.success(f"Ticket {ticket.ticket_id} assigned to {selected_staff}!")
                    st.experimental_rerun()
            st.write("---")
    else:
        st.write("No service tickets available.")

###########################################
# Staff: View and Update Assigned Tickets
###########################################

def staff_assigned_tickets():
    st.header("My Assigned Tickets")
    db = next(get_db())
    tickets = db.query(ServiceTicket).filter(ServiceTicket.assigned_to == st.session_state.user["user_id"]).all()
    if tickets:
        for ticket in tickets:
            st.write(f"**Ticket ID:** {ticket.ticket_id}")
            st.write(f"**Service Type:** {ticket.service_type}")
            st.write(f"**Description:** {ticket.description}")
            st.write(f"**Status:** {ticket.status}")
            if ticket.status != "Completed":
                if st.button(f"Mark Ticket {ticket.ticket_id} as Completed", key=f"complete_{ticket.ticket_id}"):
                    ticket.status = "Completed"
                    db.commit()
                    st.success(f"Ticket {ticket.ticket_id} marked as Completed!")
                    st.experimental_rerun()
            st.write("---")
    else:
        st.write("No tickets assigned to you.")

###########################################
# Admin/Manager: Attendance Report
###########################################

def attendance_report():
    st.header("Attendance Report")
    db = next(get_db())
    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date.today())
    if st.button("Generate Report"):
        records = db.query(Attendance).filter(Attendance.date.between(start_date, end_date)).all()
        if records:
            for rec in records:
                st.write(f"**User ID:** {rec.user_id} | **Date:** {rec.date} | **Check In:** {rec.check_in} | **Check Out:** {rec.check_out}")
        else:
            st.write("No attendance records found for the selected period.")

###########################################
# Dashboard Routing Based on User Role
###########################################

def dashboard():
    st.sidebar.title("Menu")
    role = st.session_state.user["role"]

    if role == "admin":
        menu = st.sidebar.radio("Select an option", ["Dashboard", "Register User", "Attendance Report", "Manage Service Tickets"])
        if menu == "Dashboard":
            st.header("Admin Dashboard")
            st.write("Overview of system metrics and recent activity...")
        elif menu == "Register User":
            register_user()
        elif menu == "Attendance Report":
            attendance_report()
        elif menu == "Manage Service Tickets":
            manager_service_tickets()

    elif role == "manager":
        menu = st.sidebar.radio("Select an option", ["Dashboard", "Attendance Report", "Manage Service Tickets"])
        if menu == "Dashboard":
            st.header("Manager Dashboard")
            st.write("Overview of operations...")
        elif menu == "Attendance Report":
            attendance_report()
        elif menu == "Manage Service Tickets":
            manager_service_tickets()

    elif role == "staff":
        menu = st.sidebar.radio("Select an option", ["Dashboard", "Mark Attendance", "My Assigned Tickets"])
        if menu == "Dashboard":
            st.header("Staff Dashboard")
            st.write("Overview of your tasks and attendance...")
        elif menu == "Mark Attendance":
            staff_attendance()
        elif menu == "My Assigned Tickets":
            staff_assigned_tickets()

    elif role == "client":
        menu = st.sidebar.radio("Select an option", ["Dashboard", "Raise Service Request", "My Service Tickets"])
        if menu == "Dashboard":
            st.header("Client Dashboard")
            st.write("Overview of your service requests...")
        elif menu == "Raise Service Request":
            client_service_request()
        elif menu == "My Service Tickets":
            client_view_tickets()

    st.sidebar.button("Logout", on_click=logout)

###########################################
# Main Application
###########################################

def main():
    # If not logged in, show the login page.
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()



from datetime import date
from sqlalchemy.orm import sessionmaker
from main import engine, User, create_user  # Adjust the import if your file/module name is different

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Define the admin user data.
user_data = {
    "full_name": "Admin User",
    "phone_number": "1234567890",
    "email": "admin@example.com",
    "aadhar_number": "123456789012",
    "service_domain": "",
    "role": "admin",
    "level_of_employment": "",
    "date_of_joining": date.today(),
    "salary": 0.0,
    "certifications": "",
    "password": "adminpassword"  # Use a secure password in production!
}

# Create the admin user.
create_user(db, user_data)
print("Admin user created. You can now log in using admin@example.com and password adminpassword.")


pip install streamlit sqlalchemy bcrypt
