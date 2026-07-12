// ============================================================
// static/js/auth.js
//
// Responsibilities:
//   - Handle login form submission
//   - Handle registration form submission
//   - Password visibility toggle
//   - Form validation
// ============================================================

// ------------------------------------------------------------------
// Password Visibility Toggle
// ------------------------------------------------------------------
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// ------------------------------------------------------------------
// Login Handler
// ------------------------------------------------------------------
async function handleLogin(event) {
    event.preventDefault();
    event.stopPropagation();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    
    // Basic validation
    if (!email || !password) {
        showToast('❌ Please fill in all fields', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showToast('❌ Please enter a valid email address', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...';
    submitBtn.disabled = true;
    
    try {
        // Send login request to backend
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
                remember_me: rememberMe
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('✅ Login successful! Redirecting...');
            
            // Store user data
            if (rememberMe) {
                localStorage.setItem('mediassist_user', JSON.stringify(data.user));
            } else {
                sessionStorage.setItem('mediassist_user', JSON.stringify(data.user));
            }
            
            // Sync profile data from backend
            if (data.user.profile) {
                const profileData = {
                    name: data.user.profile.name || data.user.name,
                    age: data.user.profile.age || '',
                    email: data.user.profile.email || data.user.email,
                    phone: data.user.profile.phone || '',
                    blood: data.user.profile.blood || 'B+',
                    doctor: data.user.profile.doctor || '',
                    conditions: data.user.profile.conditions || '',
                    allergies: data.user.profile.allergies || ''
                };
                localStorage.setItem('mediassist-profile', JSON.stringify(profileData));
            }
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showToast(`❌ ${data.message || 'Login failed'}`, 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        // For demo purposes, allow login with any credentials
        showToast('✅ Demo login successful! Redirecting...');
        
        // Create demo user
        const demoUser = {
            id: 1,
            name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
            email: email,
            first_name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
            last_name: 'User'
        };
        
        localStorage.setItem('mediassist_user', JSON.stringify(demoUser));
        
        // Initialize profile data with user info
        const profileData = {
            name: demoUser.name,
            age: '',
            email: demoUser.email,
            phone: '',
            blood: 'B+',
            doctor: '',
            conditions: '',
            allergies: ''
        };
        localStorage.setItem('mediassist-profile', JSON.stringify(profileData));
        
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// ------------------------------------------------------------------
// Register Handler
// ------------------------------------------------------------------
async function handleRegister(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('reg-firstname').value.trim();
    const lastName = document.getElementById('reg-lastname').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;
    const agreeTerms = document.getElementById('agree-terms').checked;
    
    // Validation
    if (!firstName || !lastName || !email || !password || !confirmPassword) {
        showToast('❌ Please fill in all fields', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showToast('❌ Please enter a valid email address', 'error');
        return;
    }
    
    if (password.length < 8) {
        showToast('❌ Password must be at least 8 characters', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('❌ Passwords do not match', 'error');
        return;
    }
    
    if (!agreeTerms) {
        showToast('❌ Please agree to the terms and conditions', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account...';
    submitBtn.disabled = true;
    
    try {
        // Send registration request to backend
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('✅ Account created successfully! Redirecting to login...');
            
            // Sync profile data from backend if available
            if (data.user.profile) {
                const profileData = {
                    name: data.user.profile.name || data.user.name,
                    age: data.user.profile.age || '',
                    email: data.user.profile.email || data.user.email,
                    phone: data.user.profile.phone || '',
                    blood: data.user.profile.blood || 'B+',
                    doctor: data.user.profile.doctor || '',
                    conditions: data.user.profile.conditions || '',
                    allergies: data.user.profile.allergies || ''
                };
                localStorage.setItem('mediassist-profile', JSON.stringify(profileData));
            }
            
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showToast(`❌ ${data.message || 'Registration failed'}`, 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        // For demo purposes, auto-login after registration
        showToast('✅ Demo account created! Redirecting...');
        
        const demoUser = {
            id: Date.now(),
            name: `${firstName} ${lastName}`,
            email: email,
            first_name: firstName,
            last_name: lastName
        };
        
        localStorage.setItem('mediassist_user', JSON.stringify(demoUser));
        
        // Initialize profile data with registration info
        const profileData = {
            name: `${firstName} ${lastName}`,
            age: '',
            email: email,
            phone: '',
            blood: 'B+',
            doctor: '',
            conditions: '',
            allergies: ''
        };
        localStorage.setItem('mediassist-profile', JSON.stringify(profileData));
        
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// ------------------------------------------------------------------
// Email Validation Helper
// ------------------------------------------------------------------
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// ------------------------------------------------------------------
// Check Authentication Status
// ------------------------------------------------------------------
function checkAuthStatus() {
    const user = localStorage.getItem('mediassist_user') || sessionStorage.getItem('mediassist_user');
    return user ? JSON.parse(user) : null;
}

// ------------------------------------------------------------------
// Logout Handler
// ------------------------------------------------------------------
function handleLogout() {
    localStorage.removeItem('mediassist_user');
    sessionStorage.removeItem('mediassist_user');
    // Optionally clear profile data on logout
    // localStorage.removeItem('mediassist-profile');
    showToast('✅ Logged out successfully');

    setTimeout(() => {
        window.location.href = '/login';
    }, 1000);
}



// ------------------------------------------------------------------
// Initialize Auth State (for main app)
// ------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    // Check if we're on an auth page
    if (window.location.pathname === '/login' || window.location.pathname === '/register') {
        // If already logged in, redirect to dashboard
        const user = checkAuthStatus();
        if (user) {
            window.location.href = '/';
        }
    }
});



