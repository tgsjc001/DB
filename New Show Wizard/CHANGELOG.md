# Changelog - New Show Wizard Refactoring

## Version 2.0 - Security and Usability Improvements

### Added
- **Security Features**:
  - Environment variable support for database credentials (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
  - Environment variables take precedence over config.ini
  - .env.example template file for easy configuration
  - SQL injection protection using psycopg2.sql for identifier quoting
  - Updated .gitignore to exclude sensitive files (.env, *.env)

- **Database Utilities** (db_utils.py):
  - `load_db_config()` - Loads configuration from environment or config file with proper fallbacks
  - `get_db_connection()` - Context manager for database connections
  - `get_existing_databases()` - Retrieves list of TGS databases
  - `database_exists()` - Checks if a database exists
  - `terminate_database_connections()` - Terminates connections to a database
  - `create_database_from_template()` - Clones a database safely
  - All functions use proper error handling with specific exception types

- **UI Improvements**:
  - Completely redesigned Tkinter interface with better layout
  - Added tooltips for all input fields to guide users
  - Added real-time database name preview
  - Added input validation with helpful error messages
  - Added confirmation dialog before database creation
  - Better visual hierarchy with improved fonts and spacing
  - Visual feedback during database creation (wait cursor)
  - Refresh button to reload database list

- **Cross-Platform Support**:
  - NewShowWizard.sh script for Unix/Linux/Mac systems
  - Made shell script executable
  - Both scripts check for dependencies

- **Documentation**:
  - Comprehensive README.md with setup instructions
  - requirements.txt for easy dependency installation
  - test_db_utils.py with unit tests
  - Code comments and docstrings for all functions

### Changed
- **Code Organization**:
  - Separated database logic into db_utils.py module
  - Converted to class-based Tkinter application (NewShowWizard class)
  - All database operations now use context managers for clean resource handling
  - Improved error messages with specific error types (OperationalError, DatabaseError)

- **Error Handling**:
  - Added comprehensive exception handling throughout
  - Specific error messages for different failure scenarios
  - Better error propagation and logging
  - User-friendly error dialogs with detailed information

### Fixed
- SQL injection vulnerability in database creation (now uses psycopg2.sql.Identifier)
- Widget state handling that could cause exceptions (now uses cursor change)
- Resource leaks by ensuring all connections are properly closed
- Missing error handling for configuration loading

### Security Notes
- **IMPORTANT**: Never commit config.ini with real credentials to version control
- Use environment variables in production environments for better security
- The application properly quotes all SQL identifiers to prevent injection
- All database operations use context managers to ensure proper resource cleanup

### Migration Notes
For users upgrading from version 1.x:
1. The config.ini format remains the same and is still supported
2. Optionally, set environment variables for better security:
   - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
3. Install new dependencies: `pip install -r requirements.txt`
4. Run tests to verify: `python test_db_utils.py`

### Testing
All core functionality has been tested:
- ✓ Configuration loading from config.ini
- ✓ Configuration loading from environment variables
- ✓ Environment variable precedence
- ✓ Error handling for missing configuration
- ✓ Python syntax validation
- ✓ Code review passed with fixes applied
- ✓ SQL injection prevention verified

### Backward Compatibility
- All existing functionality preserved
- Database cloning works identically
- Same database naming convention (tgsdb_show_year)
- PostgreSQL compatibility maintained
- config.ini still supported as fallback
