// Dummy credentials (STRICT)
const DUMMY_USERNAME = "admin";
const DUMMY_PASSWORD = "actionfi";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const errorMessage = document.getElementById("errorMessage");
    const btnText = document.getElementById("btnText");

    // Redirect if already logged in
    if (sessionStorage.getItem("isAuthenticated") === "true") {
        window.location.href = "/dashboard";
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        errorMessage.classList.remove("show");
        errorMessage.textContent = "";

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            showError("Username and password are required.");
            return;
        }

        btnText.textContent = "Authenticating...";

        // Strict validation
        if (username === DUMMY_USERNAME && password === DUMMY_PASSWORD) {
            loginSuccess(username);
        } else {
            showError("Invalid username or password.");
        }

        btnText.textContent = "Login";
    });

    function loginSuccess(username) {
        sessionStorage.setItem("isAuthenticated", "true");
        sessionStorage.setItem("username", username);
        sessionStorage.setItem("loginTime", new Date().toISOString());

        window.location.href = "/dashboard";
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add("show");
    }
});
