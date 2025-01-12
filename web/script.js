// script.js

document.addEventListener("DOMContentLoaded", () => {
    const adButton = document.getElementById("watchAdButton");

    adButton.addEventListener("click", () => {
        adButton.disabled = true;
        adButton.textContent = "Loading Ad...";

        // Call the Monetag function to show the ad
        show_8766745()
            .then(() => {
                alert("Ad watched successfully! You earned a reward.");
                adButton.textContent = "Watch Another Ad";
            })
            .catch((error) => {
                console.error("Error displaying ad:", error);
                alert("Failed to load the ad. Please try again later.");
                adButton.textContent = "Watch Ad";
            })
            .finally(() => {
                adButton.disabled = false;
            });
    });
});

// Expose an ad trigger function globally
function triggerAdSession() {
    window.show_8766745()
        .then(() => {
            console.log("Ad session completed!");
            // Optionally: Notify your server or Telegram bot
        })
        .catch((error) => {
            console.error("Error during ad session:", error);
        });
}

