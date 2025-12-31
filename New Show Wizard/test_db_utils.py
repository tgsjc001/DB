#!/usr/bin/env python3
"""
Test script for New Show Wizard functionality.
Tests database utility functions without requiring a live database connection.
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

import db_utils


def test_load_db_config_from_file():
    """Test loading configuration from config.ini"""
    print("Test 1: Load config from config.ini...")
    try:
        # Clear any environment variables first
        for key in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        config = db_utils.load_db_config()
        assert 'host' in config
        assert 'port' in config
        assert 'user' in config
        assert 'password' in config
        print("  ✓ Config loaded successfully from config.ini")
        print(f"    Host: {config['host']}")
        print(f"    Port: {config['port']}")
        print(f"    User: {config['user']}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_load_db_config_from_env():
    """Test loading configuration from environment variables"""
    print("\nTest 2: Load config from environment variables...")
    try:
        # Set environment variables
        os.environ['DB_HOST'] = 'testhost.example.com'
        os.environ['DB_PORT'] = '5433'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass123'
        
        config = db_utils.load_db_config()
        
        # Verify environment variables take precedence
        assert config['host'] == 'testhost.example.com', "Host mismatch"
        assert config['port'] == '5433', "Port mismatch"
        assert config['user'] == 'testuser', "User mismatch"
        assert config['password'] == 'testpass123', "Password mismatch"
        
        print("  ✓ Config loaded successfully from environment variables")
        print("  ✓ Environment variables take precedence over config.ini")
        
        # Clean up
        for key in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']:
            del os.environ[key]
        
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_config_error_handling():
    """Test error handling when configuration is missing"""
    print("\nTest 3: Test error handling for missing config...")
    try:
        # Clear environment variables
        for key in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']:
            if key in os.environ:
                del os.environ[key]
        
        # Temporarily rename config.ini to simulate missing config
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        temp_path = config_path + '.tmp'
        config_exists = os.path.exists(config_path)
        
        if config_exists:
            os.rename(config_path, temp_path)
        
        try:
            config = db_utils.load_db_config()
            print("  ✗ Should have raised ValueError")
            result = False
        except ValueError as e:
            print("  ✓ Correctly raises ValueError when config is missing")
            print(f"    Error message: {str(e)[:60]}...")
            result = True
        finally:
            # Restore config.ini
            if config_exists:
                os.rename(temp_path, config_path)
        
        return result
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running New Show Wizard Unit Tests")
    print("=" * 60)
    
    tests = [
        test_load_db_config_from_file,
        test_load_db_config_from_env,
        test_config_error_handling,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
