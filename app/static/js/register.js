document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const message = document.getElementById("registerMessage");

    if (!form || !message) return;

    form.addEventListener("submit", (event) => {
        const firstName = document.getElementById("first_name")?.value.trim() || "";
        const lastName = document.getElementById("last_name")?.value.trim() || "";
        const email = document.getElementById("email")?.value.trim() || "";
        const password = document.getElementById("password")?.value.trim() || "";
        const confirmPassword = document.getElementById("confirm_password")?.value.trim() || "";

        message.textContent = "";
        message.className = "form-message";

        if (!firstName || !lastName || !email || !password || !confirmPassword) {
            event.preventDefault();
            message.textContent = "Please complete all required fields.";
            message.classList.add("error");
            return;
        }

        if (!isValidEmail(email)) {
            event.preventDefault();
            message.textContent = "Please enter a valid email address.";
            message.classList.add("error");
            return;
        }

        if (password.length < 8) {
            event.preventDefault();
            message.textContent = "Password must be at least 8 characters long.";
            message.classList.add("error");
            return;
        }

        if (password !== confirmPassword) {
            event.preventDefault();
            message.textContent = "Passwords do not match.";
            message.classList.add("error");
        }
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
});
