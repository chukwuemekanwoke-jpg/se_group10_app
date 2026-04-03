document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const message = document.getElementById("registerMessage");

    if (!form) return;

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const firstName = document.getElementById("first_name").value.trim();
        const lastName = document.getElementById("last_name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phoneNumber = document.getElementById("phone_number").value.trim();
        const password = document.getElementById("password").value.trim();
        const confirmPassword = document.getElementById("confirm_password").value.trim();

        message.textContent = "";
        message.style.color = "#ff8a8a";

        if (!firstName || !lastName || !email || !phone || !password || !confirmPassword) {
            message.textContent = "Please fill in all fields.";
            return;
        }

        if (!isValidEmail(email)) {
            message.textContent = "Please enter a valid email address.";
            return;
        }

        if (!isValidPhone(phone)) {
            message.textContent = "Please enter a valid phone number.";
            return;
        }

        if (password.length < 6) {
            message.textContent = "Password must be at least 6 characters long.";
            return;
        }

        if (password !== confirmPassword) {
            message.textContent = "Passwords do not match.";
            return;
        }

        message.style.color = "#9be39b";
        message.textContent = "Registration form submitted successfully.";

        // Later replace with real fetch('/register', ...)
        setTimeout(() => {
            window.location.href = "/login";
        }, 1000);
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        return /^[0-9+\-\s()]{7,20}$/.test(phone);
    }
});