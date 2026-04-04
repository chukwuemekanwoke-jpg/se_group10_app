document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const message = document.getElementById("loginMessage");

    if (!form || !message) return;

    form.addEventListener("submit", (event) => {
        const email = document.getElementById("email")?.value.trim() || "";
        const password = document.getElementById("password")?.value.trim() || "";

        message.textContent = "";
        message.className = "form-message";

        if (!email || !password) {
            event.preventDefault();
            message.textContent = "Please enter both email and password.";
            message.classList.add("error");
            return;
        }

        if (!isValidEmail(email)) {
            event.preventDefault();
            message.textContent = "Please enter a valid email address.";
            message.classList.add("error");
            return;
        }
    });

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
});
