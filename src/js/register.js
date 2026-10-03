document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerForm');
  const errorMessage = document.getElementById('error-message');

  registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    // Clear previous error messages
    errorMessage.textContent = '';
    errorMessage.style.display = 'none';
    
    // Get form values
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const address = document.getElementById('address').value;
    const dob = document.getElementById('dob').value;
    const gender = document.getElementById('gender').value;
    const nationalId = document.getElementById('national-id').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const termsAgreed = document.getElementById('terms').checked;
    
    // Basic validation
    if (!email || !phone || !address || !dob || !gender || !nationalId || !password || !confirmPassword) {
      showError('Please fill in all fields');
      return;
    }
    
    if (!validateEmail(email)) {
      showError('Please enter a valid email address');
      return;
    }
    
    if (!validatePhone(phone)) {
      showError('Please enter a valid phone number');
      return;
    }
    
    if (password !== confirmPassword) {
      showError('Passwords do not match');
      return;
    }
    
    if (!termsAgreed) {
      showError('You must agree to the terms and conditions');
      return;
    }
    
    // Prepare data for API call
    const userData = {
      email,
      phone,
      address,
      dob,
      gender,
      national_id: nationalId,
      password
    };
    
    try {
      // Make API call to register endpoint
      const response = await fetch('http://127.0.0.1:8000/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });
      
      if (response.ok) {
        // Registration successful
        const data = await response.json();
        // Store token if provided
        if (data.token) {
          localStorage.setItem('jwtTokenVoter', data.token);
        }
        // Redirect to login page
        window.location.href = 'login.html';
      } else {
        // Registration failed
        const errorData = await response.json();
        showError(errorData.detail || 'Registration failed. Please try again.');
      }
    } catch (error) {
      showError('An unexpected error occurred. Please try again later.');
      console.error('Registration error:', error);
    }
  });
  
  // Helper functions
  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
  }
  
  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }
  
  function validatePhone(phone) {
    // Basic phone validation - can be adjusted based on requirements
    return phone.length >= 10 && /^\d+$/.test(phone);
  }
});