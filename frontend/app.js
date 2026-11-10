document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageEl = document.getElementById('message');

    try {
        // Apuesta al contenedor backend definido en el docker-compose
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            messageEl.textContent = data.message;
            messageEl.className = "mt-4 text-center text-sm font-medium text-green-600";
        } else {
            messageEl.textContent = data.message;
            messageEl.className = "mt-4 text-center text-sm font-medium text-red-600";
        }
    } catch (error) {
        messageEl.textContent = "No se pudo conectar con el servidor backend.";
        messageEl.className = "mt-4 text-center text-sm font-medium text-red-600";
    }
});
