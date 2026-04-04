document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const message = document.getElementById("loginMessage");

    if (!form || !message) return;

    form.addEventListener("submit", (event) => {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        message.textContent = "";
        message.style.color = "#ff8a8a";

        if (!email || !password) {
            event.preventDefault();
            message.textContent = "Please enter both email and password.";
            return;
        }

        if (!isValidEmail(email)) {
            event.preventDefault();
            message.textContent = "Please enter a valid email address.";
            return;
        }

        // If validation passes, allow normal form submission to Flask
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
});
