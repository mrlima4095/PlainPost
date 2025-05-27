async function conectar(acao, extra = {}) {
    const token = localStorage.getItem("Mail-Token");
    if (!token) {
        window.location.href = "login";
        return;
    }

    try {
        const resposta = await fetch("https://servidordomal.fun/api/mail", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": token
            },
            body: JSON.stringify({ action: acao, ...extra }),
        });

        const dados = await resposta.json();
        return dados.response;
    } catch {
        return;
    }
}

window.onload = () => {
    document.getElementById("back").addEventListener("click", () => {
        window.location.href = "/mail";
    });

    document.getElementById("changetag").addEventListener("click", async () => {
        const token = localStorage.getItem("Mail-Token");
        if (!token) {
            window.location.href = "login";
            return;
        }

        const roles = await conectar("roles");
        if (!roles || roles === "No roles") {
            return Swal.fire('Erro', 'Você não possui TAGs.', 'error');
        }

        const opcoes = roles.split(",").map(tag => `<option value="${tag}">${tag}</option>`).join("");

        const { value: tag } = await Swal.fire({
            title: 'Trocar TAG',
            html: `<select id="swal-trocar" class="swal2-select">${opcoes}</select>`,
            preConfirm: () => document.getElementById('swal-trocar').value,
            showCancelButton: true
        });

        if (!tag) return;

        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": token
                },
                body: JSON.stringify({ action: "changerole", role: tag }),
            });

            if (resposta.status === 200) {
                Swal.fire('Sucesso', 'TAG trocada com sucesso!', 'success');
            } else if (resposta.status === 404) {
                Swal.fire('Erro', 'Você não possui essa TAG!', 'error');
            } else if (resposta.status === 400) {
                Swal.fire('Erro', 'TAG inválida!', 'error');
            } else {
                Swal.fire('Erro', 'Erro ao trocar TAG.', 'error');
            }
        } catch {
            Swal.fire('Erro', 'Erro na conexão.', 'error');
        }
    });

    document.getElementById("buytag").addEventListener("click", async () => {
        const token = localStorage.getItem("Mail-Token");
        if (!token) {
            window.location.href = "login";
            return;
        }

        const roles = await conectar("listroles");
        if (!roles || roles === "No roles") {
            return Swal.fire('Erro', 'Nenhuma TAG disponível.', 'error');
        }

        const opcoes = roles.split("|").map(r => {
            const [tag, preco] = r.split(":");
            return `<option value="${tag}">${tag} - ${preco} moedas</option>`;
        }).join("");

        const { value: tag } = await Swal.fire({
            title: 'Comprar TAG',
            html: `<select id="swal-tag" class="swal2-select">${opcoes}</select>`,
            preConfirm: () => document.getElementById('swal-tag').value,
            showCancelButton: true
        });

        if (!tag) return;

        try {
            const resposta = await fetch("https://servidordomal.fun/api/mail", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": token
                },
                body: JSON.stringify({ action: "buyrole", role: tag }),
            });

            if (resposta.status === 200) {
                Swal.fire('Sucesso', 'TAG comprada com sucesso!', 'success');
            } else if (resposta.status === 404) {
                Swal.fire('Erro', 'TAG não disponível!', 'error');
            } else if (resposta.status === 406) {
                Swal.fire('Erro', 'Você já possui esta TAG!', 'error');
            } else if (resposta.status === 401) {
                Swal.fire('Erro', 'Saldo insuficiente!', 'error');
            } else {
                Swal.fire('Erro', 'Erro ao comprar TAG.', 'error');
            }
        } catch {
            Swal.fire('Erro', 'Erro na conexão.', 'error');
        }
    });
};
