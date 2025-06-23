/**
 * Example JavaScript file with various code issues for Meta-Refine analysis.
 * 
 * This file intentionally contains security vulnerabilities, performance issues,
 * and best practice violations to demonstrate analysis capabilities.
 */

// Security: Hardcoded API key
const API_KEY = "sk-1234567890abcdef";
const DB_PASSWORD = "admin123";

/**
 * Authentication function with security vulnerabilities
 */
function authenticateUser(username, password) {
    // Critical: XSS vulnerability
    document.getElementById("welcome").innerHTML = "Welcome " + username + "!";
    
    // Security: No CSRF protection
    return fetch("/api/login", {
        method: "POST",
        body: JSON.stringify({username, password})
    });
}

class DataProcessor {
    constructor() {
        this.cache = new Map();
        this.eventListeners = [];
    }
    
    // Performance: Memory leak - no cleanup
    processLargeDataset(data) {
        data.forEach(item => {
            // Memory: Storing large objects indefinitely
            this.cache.set(item.id, {
                original: item,
                processed: this.expensiveOperation(item),
                timestamp: Date.now()
            });
            
            // Memory leak: Adding listeners without removal
            const listener = () => this.handleUpdate(item.id);
            document.addEventListener('update', listener);
            this.eventListeners.push(listener);
        });
    }
    
    // Performance: O(n²) algorithm
    findDuplicates(array) {
        const duplicates = [];
        for (let i = 0; i < array.length; i++) {
            for (let j = i + 1; j < array.length; j++) {
                if (array[i] === array[j]) {
                    duplicates.push(array[i]);
                }
            }
        }
        return duplicates;
    }
    
    // Security: SQL injection vulnerability
    updateUserProfile(userId, profileData) {
        const query = `UPDATE users SET profile='${JSON.stringify(profileData)}' WHERE id=${userId}`;
        return executeQuery(query);
    }
    
    // Performance: Inefficient data filtering
    filterActiveUsers(users) {
        // Could use filter() method instead
        const activeUsers = [];
        for (let i = 0; i < users.length; i++) {
            if (users[i].status === 'active') {
                // Performance: Unnecessary object creation
                const userCopy = {
                    id: users[i].id,
                    name: users[i].name,
                    email: users[i].email,
                    status: users[i].status
                };
                activeUsers.push(userCopy);
            }
        }
        return activeUsers;
    }
    
    // Style: Missing error handling
    expensiveOperation(item) {
        // Performance: Synchronous operation that could block UI
        let result = 0;
        for (let i = 0; i < 1000000; i++) {
            result += Math.random() * item.value;
        }
        return result;
    }
}

// Security: Vulnerable eval usage
function executeUserScript(scriptCode) {
    // Critical: Arbitrary code execution
    return eval(scriptCode);
}

// Performance: Inefficient DOM manipulation
function updateUserList(users) {
    const container = document.getElementById('user-list');
    
    // Performance: Clearing innerHTML instead of targeted updates
    container.innerHTML = '';
    
    users.forEach(user => {
        // Performance: Creating DOM elements in loop
        const userDiv = document.createElement('div');
        userDiv.className = 'user-item';
        
        // Security: Potential XSS
        userDiv.innerHTML = `
            <h3>${user.name}</h3>
            <p>${user.bio}</p>
            <a href="${user.website}">Visit Website</a>
        `;
        
        // Performance: Adding individual event listeners
        userDiv.addEventListener('click', function() {
            handleUserClick(user.id);
        });
        
        container.appendChild(userDiv);
    });
}

// Style: Inconsistent error handling
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        
        // Error: Not checking response status
        const data = await response.json();
        return data;
    } catch (error) {
        // Error: Silent failure
        console.log("Error occurred");
        return null;
    }
}

// Security: Vulnerable cookie handling
function setUserSession(userData) {
    // Security: No secure flag on sensitive cookie
    document.cookie = `session=${JSON.stringify(userData)}; path=/`;
    
    // Security: Storing sensitive data in sessionStorage
    sessionStorage.setItem('user_token', userData.token);
    sessionStorage.setItem('user_permissions', JSON.stringify(userData.permissions));
}

// Performance: Inefficient array operations
function processNumbers(numbers) {
    // Performance: Multiple array iterations
    const doubled = numbers.map(n => n * 2);
    const filtered = doubled.filter(n => n > 10);
    const sorted = filtered.sort((a, b) => a - b);
    const summed = sorted.reduce((sum, n) => sum + n, 0);
    
    return summed;
}

// Logic: Race condition potential
let globalCounter = 0;

function incrementCounter() {
    // Concurrency: Non-atomic operation
    const current = globalCounter;
    setTimeout(() => {
        globalCounter = current + 1;
    }, Math.random() * 100);
}

// Style: Unused variables and functions
const unusedVariable = "never used";
const anotherUnused = {key: "value"};

function unusedFunction() {
    console.log("This function is never called");
}

// Performance: Expensive computation in global scope
const EXPENSIVE_ARRAY = new Array(100000).fill(0).map((_, i) => i * Math.random());

// Error: Missing input validation
function calculateDiscount(price, discountPercent) {
    // Logic: No validation of inputs
    return price * (discountPercent / 100);
}

// Security: Insecure random number generation
function generateSecretToken() {
    // Security: Math.random() is not cryptographically secure
    return Math.random().toString(36).substring(2, 15);
}

// Style: Inconsistent code formatting and no error boundaries
class ApiClient{
    constructor(baseUrl){
        this.baseUrl=baseUrl;
        this.retryCount=3;
    }
    
    async makeRequest(endpoint,options={}){
        for(let i=0;i<this.retryCount;i++){
            try{
                const response=await fetch(this.baseUrl+endpoint,options);
                if(!response.ok){
                    throw new Error(`HTTP ${response.status}`);
                }
                return await response.json();
            }catch(error){
                if(i===this.retryCount-1)throw error;
                await new Promise(resolve=>setTimeout(resolve,1000*Math.pow(2,i)));
            }
        }
    }
}

// Entry point with issues
document.addEventListener('DOMContentLoaded', function() {
    // Error: No error boundary for initialization
    const processor = new DataProcessor();
    const apiClient = new ApiClient('https://api.example.com');
    
    // Performance: Synchronous operation that could block
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    updateUserList(users);
    
    console.log("Application initialized");
}); 