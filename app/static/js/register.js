document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const message = document.getElementById("registerMessage");

    if (!form) return;

    form.addEventListener("submit", (event) => {
        // Client-side validation only — let the form POST normally if valid
        const firstName = document.getElementById("first_name").value.trim();
        const lastName = document.getElementById("last_name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phoneNumber = document.getElementById("phone_number")?.value.trim() || "";
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        message.textContent = "";
        message.style.color = "#ff8a8a";

        if (!firstName || !lastName || !email || !password || !confirmPassword) {
            event.preventDefault();
            message.textContent = "Please fill in all required fields.";
            return;
        }

        if (!isValidEmail(email)) {
            event.preventDefault();
            message.textContent = "Please enter a valid email address.";
            return;
        }

        if (phoneNumber && !isValidPhone(phoneNumber)) {
            event.preventDefault();
            message.textContent = "Please enter a valid phone number.";
            return;
        }

        if (password.length < 8) {
            event.preventDefault();
            message.textContent = "Password must be at least 8 characters long.";
            return;
        }

        if (password !== confirmPassword) {
            event.preventDefault();
            message.textContent = "Passwords do not match.";
            return;
        }

        // Validation passed — allow normal form POST (CSRF token included in hidden field)
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        return /^[0-9+\-\s()]{7,20}$/.test(phone);
    }
});
