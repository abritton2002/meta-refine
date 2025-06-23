import os
import sys

def bad_function():
    password = "admin123"  # Hardcoded password
    try:
        result = 10 / 0  # Division by zero
    except:  # Bare except clause
        pass
    
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name='{input()}'"
    
    for i in range(1000000):  # Inefficient loop
        print(i)

# Unused variable
unused_var = "not used"

def function_with_no_docs():
    return True
