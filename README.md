# Gym Management Project - Local Setup

This is a Django application for gym management. Follow these steps to run it locally on your Windows system.

## Prerequisites

- Python 3.11 or later installed.

## Setup Instructions

1. **Navigate to the project directory**: Open Command Prompt and change to the project directory:  
   `cd c:\projects\test`

2. **Create a virtual environment**: Create a virtual environment to isolate the project dependencies:  
   `python -m venv venv`

3. **Activate the virtual environment**: Activate the virtual environment:  
   `venv\Scripts\activate`

4. **Install dependencies**: Install the required packages using pip:  
   `pip install -r requirements.txt`

5. **Run database migrations**: Apply any pending migrations to set up the database:  
   `python manage.py migrate`

6. **Start the development server**: Run the Django development server:  
   `python manage.py runserver`

7. **Access the application**: Open a web browser and go to `http://127.0.0.1:8000/` to view the application.

8. **Deactivate the virtual environment** (when done): To exit the virtual environment, run:  
   `deactivate`

## Notes

- The project uses SQLite as the database.
- DEBUG mode is enabled for local development.
- If you encounter any issues, ensure all dependencies are installed correctly and check for any error messages in the console.
