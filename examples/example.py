"""
Example Python file with various code issues for Meta-Refine analysis.

This file intentionally contains bugs, security vulnerabilities, performance issues,
and style problems to demonstrate Meta-Refine's analysis capabilities.
"""

import os
import sys
import hashlib
import requests

# Security issue: hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

def vulnerable_login(username, password):
    """Login function with security vulnerabilities."""
    
    # Critical: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    # High: Password not hashed
    if password == DATABASE_PASSWORD:
        return True
    
    # Medium: Unhandled exception potential
    result = execute_query(query)
    return result[0]['authenticated']

class UserManager:
    """User management class with performance issues."""
    
    def __init__(self):
        self.users = []
        self.user_cache = {}
    
    def add_user(self, user):
        """Add user with inefficient duplicate checking."""
        # Performance: O(n) search that could use a set
        for existing_user in self.users:
            if existing_user.id == user.id:
                return False
        
        self.users.append(user)
        return True
    
    # Style: Missing docstring
    def get_user_count(self):
        return len(self.users)
    
    def find_users_by_department(self, department):
        """Find users by department - inefficient implementation."""
        # Performance: O(n²) nested loops
        results = []
        for user in self.users:
            for dept in user.departments:
                if dept.name == department:
                    # Memory: Creating unnecessary copies
                    user_copy = {
                        'id': user.id,
                        'name': user.name,
                        'department': dept.name
                    }
                    results.append(user_copy)
        return results
    
    def bulk_update_users(self, updates):
        """Bulk update with poor error handling."""
        # Error handling: No transaction rollback
        for user_id, data in updates.items():
            try:
                user = self.find_user(user_id)
                user.update(data)
                self.save_user(user)
            except:  # Style: Bare except clause
                pass  # Error: Silent failure

def read_config_file(filename):
    """Read configuration with poor error handling."""
    # Error handling: No exception handling
    with open(filename, 'r') as f:
        content = f.read()
    
    # Security: Using eval on user input
    config = eval(content)
    return config

def process_user_data(data_list):
    """Process user data with various issues."""
    processed = []
    
    # Performance: Unnecessary list comprehension conversion
    data_list = [item for item in data_list]
    
    for item in data_list:
        # Style: Long conditional without helper function
        if item.get('type') == 'premium' and item.get('status') == 'active' and item.get('subscription_end') > time.time() and item.get('payment_status') == 'current':
            
            # Security: Potential path traversal
            file_path = f"/data/users/{item.get('user_id')}/{item.get('filename')}"
            
            # Error handling: File operations without try-catch
            with open(file_path, 'w') as f:
                f.write(str(item))
            
            processed.append(item)
    
    return processed

class DatabaseConnection:
    """Database connection with resource management issues."""
    
    def __init__(self, connection_string):
        self.connection = create_connection(connection_string)
        self.queries_executed = 0
    
    def execute_query(self, query, params=None):
        """Execute query with security issues."""
        # Security: String formatting in SQL
        if params:
            query = query.format(**params)
        
        # Resource management: No connection pooling
        cursor = self.connection.cursor()
        cursor.execute(query)
        
        # Memory: Not closing cursor
        return cursor.fetchall()
    
    # Style: Missing __del__ or context manager

def calculate_user_score(user_data):
    """Calculate user score with logic issues."""
    score = 0
    
    # Logic: Potential division by zero
    activity_score = user_data['total_actions'] / user_data['days_active']
    
    # Logic: Inconsistent type handling
    if user_data['premium_status']:
        score += 50
    elif user_data['premium_status'] == 'trial':  # This won't execute
        score += 25
    
    # Performance: Unnecessary regex for simple check
    import re
    if re.match(r'^admin', user_data['username']):
        score += 100
    
    return score

# Style: Unused imports and variables
import json
import time
unused_variable = "This variable is never used"
another_unused = {"key": "value"}

# Global variable that could cause issues
current_user = None

def get_user_permissions(user_id):
    """Get user permissions with race condition potential."""
    global current_user
    
    # Concurrency: Race condition with global variable
    current_user = fetch_user(user_id)
    permissions = []
    
    # Logic: Time-of-check vs time-of-use
    if current_user and current_user.is_active():
        time.sleep(0.1)  # Simulating delay
        if current_user.is_active():  # State might have changed
            permissions = current_user.get_permissions()
    
    return permissions

# Performance: Expensive operation in module scope
EXPENSIVE_COMPUTATION = sum(range(1000000))

def main():
    """Main function with various issues."""
    # Style: Hard-coded values
    users = UserManager()
    
    # Error: Not checking if file exists
    config = read_config_file('/etc/myapp/config.py')
    
    # Security: Using requests without SSL verification
    response = requests.get('https://api.example.com/data', verify=False)
    
    print("Application started")

if __name__ == "__main__":
    main() 