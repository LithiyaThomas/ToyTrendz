// Login Logic for Sign-In Page
document.getElementById('login').addEventListener('click', function() {
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    if (username && password) {
        // Add your login logic here
        alert('Logging in with username: ' + username);
        // Redirect to dashboard or another page upon successful login
    } else {
        alert('Please enter both username and password');
    }
});

// Join Us Logic for Sign-In Page
//document.getElementById('join_us').addEventListener('click', function() {
//    window.location.href = "/user_register/";  // Redirect to Join Us page
//});
