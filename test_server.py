from waitress import serve
from gym_management.wsgi import application # Change 'your_project_name' to your folder name

if __name__ == "__main__":
    print("Server is starting...")
    print("Internal Access: http://localhost:8000")
    # This '0.0.0.0' tells Waitress to listen to all network interfaces
    serve(application, host='0.0.0.0', port=8000)