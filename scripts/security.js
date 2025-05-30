window.onload = () => {
    const token = localStorage.getItem("Mail-Token");
    if (!token) { window.location.href = "login"; return; }

    document.getElementById("back").addEventListener("click", () => { window.location.href = "/mail"; });
    document.getElementById("changepass").addEventListener("click", async () => { 
        const token = localStorage.getItem("Mail-Token");
        if (!token) { window.location.href = "login"; return; }

        const { value: newpass } = await Swal.fire({ title: "Trocar Senha", input: "password", inputPlaceholder: "Nova senha", showCancelButton: true });
        if (!newpass) return;

        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify({ action: "changepass", newpass }) });

            if (resposta.status === 200) { Swal.fire("Sucesso", "Senha alterada com sucesso!", "success"); } 
            else { Swal.fire("Erro", "Erro ao trocar senha.", "error"); }
        } catch { Swal.fire("Erro", "Erro na conexão.", "error"); }
    });

    document.getElementById("signout").addEventListener("click", async () => { localStorage.removeItem("Mail-Token"); window.location.href = "login"; });
    document.getElementById("signoff").addEventListener("click", async () => { 
        const token = localStorage.getItem("Mail-Token");
        if (!token) { window.location.href = "login"; return; }

        const result = await Swal.fire({ title: "Tem certeza?", text: "Tem certeza que deseja apagar sua conta?", icon: "warning", showCancelButton: true, confirmButtonText: "Sim, apagar", cancelButtonText: "Cancelar" });
        if (!result.isConfirmed) return;

        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", { method: "POST", headers: { "Content-Type": "application/json", "Authorization": token }, body: JSON.stringify({ action: "signoff" }) });

            if (resposta.status === 200) { 
                localStorage.removeItem("Mail-Token");
                await Swal.fire("Conta apagada!", "Sua conta foi removida com sucesso.", "success");
                window.location.href = "login";
            } 
            else { Swal.fire("Erro", "Erro ao apagar conta.", "error"); }
        } catch { Swal.fire("Erro", "Erro na conexão.", "error"); }
    });
};
