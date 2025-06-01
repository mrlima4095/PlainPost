document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("Mail-Token");
    if (!token) { window.location.href = "login"; return; }

    document.getElementById("back").addEventListener("click", () => {
        window.location.href = "/mail";
    });

    document.getElementById("mural").addEventListener("click", async () => {
        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": token
                },
                body: JSON.stringify({ action: "status" }),
            });
            const dados = await resposta.json();
            if (resposta.status == 200)
                window.location.href = "/mural/" + dados.response;
            else if (resposta.status == 401)
                window.location.href = "/mail";
            else
                Swal.fire('Erro', 'Ocorreu um erro interno.', 'error');
        } catch {
            Swal.fire('Erro', 'Erro na conexão.', 'error');
        }
    });
    

    document.getElementById("changebio").addEventListener("click", async () => {
        const { value: content } = await Swal.fire({
            title: 'Biografia:',
            input: 'text',
            inputPlaceholder: 'O que esta pensando?',
            showCancelButton: true
        });
        if (!content) return Swal.fire('Erro', 'Sua biografia não pode estar vazia!', 'error');

        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": token
                },
                body: JSON.stringify({ action: "changebio", bio: content }),
            });
            if (resposta.status == 200)
                Swal.fire('Sucesso', 'Sua biografia foi alterada!', 'success');
            else if (resposta.status == 401)
                Swal.fire('Erro', 'O destinatário não foi encontrado!', 'error');
            else
                Swal.fire('Erro', 'Erro ao alterar sua biografia.', 'error');
        } catch {
            Swal.fire('Erro', 'Erro na conexão.', 'error');
        }
    });

    document.getElementById("changepage").addEventListener("click", async () => {
        alert("Clique detectado");
    });
});