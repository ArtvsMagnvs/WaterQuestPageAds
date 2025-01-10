// script.js

// Constante para almacenar la clave de Monetag desde variables de entorno
const MONETAG_ZONE_ID = process.env.MONETAG_ZONE_ID;

// Función que maneja el clic en el botón para mostrar el anuncio
function handleAdClick() {
    // Verificar si la constante está definida
    if (!MONETAG_ZONE_ID) {
        console.error("El valor de MONETAG_ZONE_ID no está configurado.");
        alert("No se puede cargar el anuncio en este momento. Por favor, inténtalo de nuevo.");
        return;
    }

    // Deshabilitar el botón para evitar clics repetidos
    const button = document.querySelector("button");
    button.disabled = true;
    button.textContent = "Cargando anuncio...";

    // Llamada dinámica a Monetag para mostrar el anuncio
    window[`show_${MONETAG_ZONE_ID}`]()
        .then(() => {
            // Si el anuncio se ha visto con éxito, redirigir al bot de Telegram
            redirectToTelegram();
        })
        .catch((error) => {
            // Manejar cualquier error que ocurra al cargar el anuncio
            console.error("Error al cargar el anuncio:", error);
            handleAdError();
        })
        .finally(() => {
            // Volver a habilitar el botón después de 5 segundos, incluso si hubo error
            setTimeout(() => {
                button.disabled = false;
                button.textContent = "Ir a mi Bot de Telegram";
            }, 5000);
        });
}

// Función que redirige al usuario al bot de Telegram
function redirectToTelegram() {
    window.location.href = "https://t.me/WaterQuestBot";
}

// Función que maneja el caso de error al cargar el anuncio
function handleAdError() {
    // Mostrar un mensaje de error amigable al usuario
    alert("Hubo un problema al cargar el anuncio. Por favor, inténtalo de nuevo.");
}

// Agregar el evento de clic al botón cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("button");
    if (button) {
        button.addEventListener("click", handleAdClick);
    } else {
        console.error("Botón no encontrado en el DOM.");
    }
});

