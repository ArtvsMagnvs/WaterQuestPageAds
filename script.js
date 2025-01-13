// script.js

document.getElementById('watch-ad-button').addEventListener('click', async () => {
    try {
        await show_8766745(); // Mostrar anuncio
        rewardUser(); // Recompensar al usuario después del anuncio
        alert('¡Gracias por ver el anuncio! Has recibido tu recompensa.');
    } catch (error) {
        console.error('Error mostrando el anuncio:', error);
        alert('El anuncio no se pudo cargar. Intenta más tarde.');
    }
});

// Función para recompensar al usuario
function rewardUser() {
    // Incrementar monedas, recursos o dar acceso a funcionalidades premium
    console.log('Recompensando al usuario...');
    // Aquí puedes llamar a una API o actualizar el estado del usuario
}

