# BusKing

BusKing is a bus booking system built with React Native for the frontend and Django for the backend. This application allows users to browse available buses, view bus details, and book tickets. The backend manages buses, users, bookings, and provides authentication features.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
+
## Features

- User authentication (register, login, logout)
- Browse available buses
- View bus details
- Book bus tickets
- View and manage bookings
- Image upload for buses and user profiles



## Installation

### Prerequisites

- Node.js and npm
- Python and pip
- React Native CLI
- Android Studio / Xcode (for running the app on a simulator or device)

### Backend Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/biokeyper/busking.git
    cd busking/backend
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

6. Run the development server:

    ```bash
    python manage.py runserver
    ```

### Frontend Setup

1. Navigate to the BuskingApp directory:

    ```bash
    cd ../BuskingApp
    ```

2. Install the required dependencies:

    ```bash
    npm install
    ```
   

4. Run the app:

    ```bash
    npx react-native run-android  # For Android
    npx react-native run-ios      # For iOS
    ```

## Usage

### User Authentication

- Register: Create a new user account.
- Login: Authenticate and obtain a token.
- Logout: Invalidate the current token.

### Bus Management

- View available buses.
- View details of a specific bus.
- Book tickets for a bus.

### Booking Management

- View list of bookings.
- View details of a specific booking.

## API Endpoints

### Auth

- `POST /api/auth/register/` - Register a new user.
- `POST /api/auth/login/` - Login and obtain a token.
- `POST /api/auth/logout/` - Logout and invalidate the token.

### Buses

- `GET /api/buses/` - List all buses.
- `GET /api/buses/:id/` - Get details of a specific bus.

### Bookings

- `GET /api/bookings/` - List all bookings.
- `POST /api/bookings/` - Create a new booking.
- `GET /api/bookings/:id/` - Get details of a specific booking.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch with a descriptive name.
3. Make your changes.
4. Commit and push your changes to your forked repository.
5. Create a pull request to the main repository.

Project Requirements for the Bus Booking System!!

Creating a project requirements document for a bus booking system involves detailing the functional and non-functional requirements, user roles, and system architecture. Here's a comprehensive outline

Project Requirements Document for Bus Booking System

1. Project Overview

Project Name: Bus Booking System
Purpose: To provide a platform for users to book bus tickets online, manage bus bookings, and handle payments efficiently.

Technology Stack:

Frontend: React Native
Backend: Django
Database: PostgresSQL
Payment Gateway: Stripe (or any preferred payment gateway)

2. Functional Requirements
2.1 User Roles
Guest User: Browse buses, view Bookings, and check seat availability.
Registered User: Book tickets, view booking history, cancel bookings, and manage profile.
Admin: Manage buses, schedules, routes, users, and view booking statistics.

2.2 User Stories
Guest User
View available buses and routes without logging in.
Check seat availability for a specific bus route.
Register and log in to the system.
Registered User

Log in to the system.
Search for buses based on source, destination, and date.
View bus details, seat availability, and fare.
Book a ticket by selecting seats and making payment.
View booking history and details of past and upcoming trips.
Cancel a booking and request a refund.
Edit personal profile information.
Admin

Log in to the admin dashboard.
Add, edit, or delete bus information.
Manage bus schedules, including dates, times, and routes.
View and manage registered users.
Monitor booking statistics and generate reports.

2.3 Detailed Functional Requirements
Bus Management:

Add new buses with details such as bus number, type, capacity, and amenities.
Edit or delete existing bus details.

Schedule Management:

Create and manage bus bookings with source, destination, departure time, and arrival time.
Assign buses to specific schedules.

Booking Management:

Search for available buses based on source, destination, and travel date.
View detailed bus schedule and seat map.
Select and book available seats.
Make online payments through integrated payment gateway.
Generate electronic tickets and send booking confirmation via email/SMS.

User Management:

User registration and authentication.
Profile management with personal information updates.
View booking history and manage bookings.

Payment Management:

Integration with payment gateway for handling payments.
Securely process transactions.
Handle refunds for canceled bookings.

3. Non-Functional Requirements
Performance: The system should handle a high number of simultaneous users efficiently.
Security: Ensure data protection through encryption, secure authentication, and secure payment processing.
Usability: The user interface should be intuitive and accessible on both mobile and web platforms.
Scalability: The system should be scalable to accommodate future growth in the number of users and transactions.
Reliability: Ensure high availability and minimal downtime.

4. System Architecture
Frontend (React Native):

User interface components for browsing, booking, and managing tickets.
Interaction with backend via RESTful APIs.

Backend (Django):

RESTful API endpoints for handling requests from the frontend.
Business logic for booking, user management, and schedule management.
Database models for storing user data, bus details, schedules, and bookings.
Database (PostgreSQL):

Store all data related to users, buses, schedules, and bookings.
Ensure data integrity and consistency.
Payment Gateway (Stripe):

Handle secure payment transactions.
Provide APIs for integrating payment processing in the booking workflow.

5. API Endpoints
User Authentication:

POST /api/register/ - Register a new user
POST /api/login/ - Log in a user
GET /api/profile/ - Get user profile
PUT /api/profile/ - Update user profile

Bus Management:

GET /api/buses/ - Get all buses
POST /api/buses/ - Add a new bus
PUT /api/buses/{id}/ - Update bus details
DELETE /api/buses/{id}/ - Delete a bus

Schedule Management:

GET /api/schedules/ - Get all schedules
POST /api/schedules/ - Add a new schedule
PUT /api/schedules/{id}/ - Update schedule details
DELETE /api/schedules/{id}/ - Delete a schedule

Booking Management:

POST /api/bookings/ - Create a new booking
GET /api/bookings/ - Get user bookings
DELETE /api/bookings/{id}/ - Cancel a booking

6. Milestones and Timeline
   
Phase 1: Requirements gathering and planning (2 weeks)

Phase 2: Design and prototyping (3 weeks)

Phase 3: Frontend and backend development (8 weeks)

Phase 4: Integration and testing (4 weeks)

Phase 5: Deployment and go-live (2 weeks)

Phase 6: Post-launch support and maintenance (Ongoing)

This document serves as a blueprint for developing the bus booking system, outlining the core features, user roles, and technical architecture necessary to build a robust and user-friendly application.

God Bless! 2024, 
Designed by Angry Coder.


## Contact

If you have any questions or suggestions, feel free to reach out:


- GitHub: [[calvinoke](https://github.com/calvinoke)](https://github.com/biokeyper/BusKing/
# BusKing-Backend
