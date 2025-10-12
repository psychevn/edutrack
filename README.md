# Assessment Management System

A comprehensive assessment management system built with Flet (Python) and SQLite database. This system allows administrators to create and manage assessments while students can take exams and view their results.

## Features

### Admin Features
- **Login Module**: Secure authentication with role-based access
- **Assessment Creation**: Create exams with multiple choice and short answer questions
- **Assessment Management**: Edit, delete, and manage existing assessments
- **Results Management**: View student submissions, grade answers, and generate reports
- **Export Functionality**: Export results to CSV/Excel format

### Student Features
- **Student Dashboard**: View available and completed assessments
- **Exam Taking**: Take timed exams with real-time timer
- **Results Viewing**: View exam results and feedback
- **Past Exams**: Review previously completed assessments

## Technology Stack

- **Frontend**: Flet (Python-based UI framework)
- **Backend**: Python with SQLite database
- **Styling**: Minimalist light blue gradient theme with icons
- **Database**: SQLite for data persistence

## Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd OS-PROJECT
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

## Default Login Credentials

### Admin Account
- **Username**: admin
- **Password**: admin123
- **Role**: Administrator (can create and manage assessments)

### Student Account
- **Username**: student
- **Password**: student123
- **Role**: Student (can take exams and view results)

## Project Structure

```
OS-PROJECT/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── pages/                 # UI pages
│   ├── __init__.py
│   ├── login_page.py      # Login interface
│   ├── admin_dashboard.py # Admin dashboard and management
│   └── student_dashboard.py # Student dashboard and exam taking
├── database/              # Database management
│   ├── __init__.py
│   └── database_manager.py # SQLite database operations
└── assessment_system.db   # SQLite database (created automatically)
```

## Usage

### For Administrators

1. **Login** with admin credentials
2. **Create Assessment**:
   - Click "Create Assessment" in the navigation
   - Fill in assessment details (title, description, duration, etc.)
   - Add questions (MCQ or short answer)
   - Save the assessment

3. **Manage Assessments**:
   - View all created assessments
   - Edit or delete existing assessments
   - View student submissions and results

4. **View Results**:
   - Access student submissions
   - Grade short answer questions manually
   - Export results to CSV/Excel

### For Students

1. **Login** with student credentials
2. **View Available Exams**:
   - See all available assessments
   - Check exam duration and details

3. **Take Exam**:
   - Click "Take Exam" on any available assessment
   - Answer questions within the time limit
   - Submit when complete or when time runs out

4. **View Results**:
   - Check your exam results
   - Review past exam performance

## Database Schema

The system uses SQLite with the following main tables:

- **users**: User accounts (admin/student)
- **assessments**: Assessment/exam information
- **questions**: Individual questions within assessments
- **submissions**: Student exam submissions
- **answers**: Individual answers to questions

## Customization

### Adding New Question Types
Extend the `question_type` field in the database and update the UI components in the respective dashboard files.

### Styling
Modify the color scheme and styling in the page files. The current theme uses a light blue gradient with minimalist design.

### Database
The SQLite database is automatically created on first run. To reset the database, simply delete the `assessment_system.db` file.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed using `pip install -r requirements.txt`

2. **Database Issues**: Delete `assessment_system.db` to reset the database

3. **UI Not Loading**: Check that Flet is properly installed and the Python version is compatible

### Support

For issues or questions, please check the error messages in the console output or contact the development team.

## Future Enhancements

- Real-time notifications
- Advanced reporting and analytics
- Bulk question import/export
- Email notifications for results
- Mobile-responsive design
- Advanced timer features
- Question randomization
- Multiple exam attempts
