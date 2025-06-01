window.onload = () => {
    const token = localStorage.getItem("Mail-Token");
    if (!token) { window.location.href = "login"; return; }

    document.getElementById("back").addEventListener("click", () => { window.location.href = "/mail"; });   
    document.getElementById("changebio").addEventListener("click", async () => {
        const { value: content } = await Swal.fire({ title: 'Biografia:', input: 'text', inputPlaceholder: 'O que esta pensando?', showCancelButton: true });
        if (!content) return Swal.fire('Erro', 'Sua biografia não pode estar vazia!', 'error');
        
        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": token },
                body: JSON.stringify({ action: "changebio", bio: content }),
            });

            if (resposta.status == 200) Swal.fire('Sucesso', 'Sua biografia foi alterada!', 'success');
            else if (resposta.status == 401) Swal.fire('Erro', 'O destinatário não foi encontrado!', 'error');
            else Swal.fire('Erro', 'Erro ao alterar sua biografia.', 'error');
        } catch { Swal.fire('Erro', 'Erro ao procurar.', 'error'); }
    });
    document.getElementById("app").addEventListener("click", () => { window.open("https://apk.e-droid.net/apk/app3599871-8b35ha.apk?v=2", "_blank"); });   
    
};
