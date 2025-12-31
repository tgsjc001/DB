# TGS New Show Database Wizard

A database management tool for creating new TGS show databases by cloning existing PostgreSQL databases.

## Features

- **Secure Configuration**: Uses environment variables for database credentials with fallback to config.ini
- **User-Friendly Interface**: Improved Tkinter GUI with tooltips and input validation
- **Robust Error Handling**: Detailed error messages for different failure scenarios
- **Context Managers**: Clean resource management for database connections
- **Cross-Platform**: Works on both Windows and Unix-based systems

## Setup

### Prerequisites

- Python 3.x
- PostgreSQL database server
- psycopg2 library

### Installation

1. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install psycopg2-binary
   ```

2. Configure database credentials using **one** of these methods:

   **Option A: Environment Variables (Recommended)**
   ```bash
   # On Unix/Linux/Mac
   export DB_HOST=10.0.0.6
   export DB_PORT=5212
   export DB_USER=TGSAdmin
   export DB_PASSWORD=your_password

   # On Windows (Command Prompt)
   set DB_HOST=10.0.0.6
   set DB_PORT=5212
   set DB_USER=TGSAdmin
   set DB_PASSWORD=your_password

   # On Windows (PowerShell)
   $env:DB_HOST="10.0.0.6"
   $env:DB_PORT="5212"
   $env:DB_USER="TGSAdmin"
   $env:DB_PASSWORD="your_password"
   ```

   **Option B: Configuration File**
   
   Copy `.env.example` to create a `config.ini` file (if it doesn't exist):
   ```ini
   [postgres]
   host = 10.0.0.6
   port = 5212
   user = TGSAdmin
   password = your_password
   ```

   **Security Note**: If using `config.ini`, ensure it's not committed to version control. Environment variables are more secure for production environments.

## Usage

### On Windows

Double-click `NewShowWizard.bat` or run from command line:
```cmd
NewShowWizard.bat
```

### On Unix/Linux/Mac

Run the shell script:
```bash
./NewShowWizard.sh
```

Or run directly with Python:
```bash
python3 ChangeDBscript.py
```

### Using the Application

1. **Select Show**: Choose between "apr" (April) or "nov" (November)
2. **Select Year**: Choose the year for the new show database
3. **Clone From**: Select an existing database to use as a template
4. **Preview**: The "New Database" field shows what the database will be named
5. **Create Database**: Click to create the new database
6. **Refresh List**: Click to reload the list of available databases

The application will:
- Validate your selections
- Ask for confirmation before creating the database
- Terminate any existing connections to the template database
- Clone the template to create the new database
- Display success or error messages

## Architecture

### File Structure

```
New Show Wizard/
├── ChangeDBscript.py    # Main application with Tkinter GUI
├── db_utils.py          # Database utility functions
├── config.ini           # Database configuration (optional, not in version control)
├── .env.example         # Example environment variables
├── requirements.txt     # Python package dependencies
├── test_db_utils.py     # Unit tests for database utilities
├── NewShowWizard.bat    # Windows launcher script
├── NewShowWizard.sh     # Unix/Linux launcher script
└── README.md            # This file
├── NewShowWizard.bat    # Windows launcher script
└── NewShowWizard.sh     # Unix/Linux launcher script
```

### Key Components

- **db_utils.py**: Provides reusable database functions with proper error handling:
  - `load_db_config()`: Loads configuration from environment or file
  - `get_db_connection()`: Context manager for database connections
  - `get_existing_databases()`: Retrieves list of TGS databases
  - `create_database_from_template()`: Clones a database

- **ChangeDBscript.py**: Main application with:
  - Improved Tkinter UI with better layout
  - Input validation
  - Tooltips for user guidance
  - Comprehensive error handling

## Error Handling

The application provides specific error messages for:
- Connection failures
- Missing configuration
- Database already exists
- Invalid input
- Query execution errors

## Security Considerations

1. **Never commit** `config.ini` with real credentials to version control
2. **Use environment variables** in production environments
3. The `.gitignore` file is configured to exclude sensitive files
4. The `.env.example` file provides a template without real credentials

## Troubleshooting

### "psycopg2 module not found"
Install the psycopg2 library:
```bash
pip install psycopg2-binary
```

### "Failed to connect to database server"
- Verify database server is running
- Check host and port in configuration
- Verify network connectivity
- Confirm credentials are correct

### "No TGS databases found"
- Ensure at least one database matching pattern `tgsdb_%_%` exists
- Check database permissions for the user

## Development

To modify or extend the application:

1. All database operations should use the `db_utils.py` functions
2. Always use context managers (`with` statements) for database connections
3. Add appropriate error handling with specific exception types
4. Follow existing code style and conventions

## License

This is internal TGS software for database management.
