async function conectar(acao, extra = {}) {
    const token = localStorage.getItem("Mail-Token");
    if (!token) { window.location.href = "login"; return; }

    try {
        const resposta = await fetch("https://servidordomal.fun/api/mail", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": token },
            body: JSON.stringify({ action: acao, ...extra }),
        });

        const dados = await resposta.json();
        return dados.response;
    } catch {
        return;
    }
}

window.onload = () => {
    const token = localStorage.getItem("Mail-Token");
    if (!token) { window.location.href = "login"; return; }

    document.getElementById("back").addEventListener("click", () => { window.location.href = "/mail"; });   
    document.getElementById("changebio").addEventListener("click", async () => {
        const { value: content } = await Swal.fire({ title: 'Biografia:', input: 'text', inputPlaceholder: 'O que esta pensando?', showCancelButton: true });
        if (!content) return Swal.fire('Erro', 'Sua biografia não pode estar vazia!', 'error');

        const { status } = await fetchRequest("changebio", { bio: content });
        if (status === 200) Swal.fire('Sucesso', 'Sua biografia foi alterada!', 'success');
        else if (status === 404) Swal.fire('Erro', 'O destinatário não foi encontrado!', 'error');
        else Swal.fire('Erro', 'Erro ao alterar sua biografia.', 'error');
    });
};
