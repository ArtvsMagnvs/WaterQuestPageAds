// Variable global para almacenar la cantidad de oro del usuario
let gold = 0;

// Manejo del botón de ver anuncios
document.getElementById('watch-ad-button').addEventListener('click', async () => {
    try {
        await show_8766745(); // Mostrar anuncio
        rewardUser(); // Recompensar al usuario después del anuncio
        alert(`¡Gracias por ver el anuncio! Has recibido 500 de oro. Tu oro total es ahora: ${gold}.`);
    } catch (error) {
        console.error('Error mostrando el anuncio:', error);
        alert('El anuncio no se pudo cargar. Intenta más tarde.');
    }
});

// Función para recompensar al usuario
function rewardUser() {
    const rewardAmount = 500; // Cantidad de oro por ver el anuncio
    gold += rewardAmount; // Incrementar la cantidad de oro del usuario
    console.log(`Recompensa añadida: ${rewardAmount}. Total de oro: ${gold}`);
}

