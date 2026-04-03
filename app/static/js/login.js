document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const message = document.getElementById("loginMessage");

    if (!form) return;

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        message.textContent = "";
        message.style.color = "#ff8a8a";

        if (!email || !password) {
            message.textContent = "Please enter both email and password.";
            return;
        }

        if (!isValidEmail(email)) {
            message.textContent = "Please enter a valid email address.";
            return;
        }

        message.style.color = "#9be39b";
        message.textContent = "Login form submitted successfully.";

        // Later you can replace this with a real fetch('/login', ...)
        // Example:
        // form.submit();

        setTimeout(() => {
            window.location.href = "/map";
        }, 800);
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
});