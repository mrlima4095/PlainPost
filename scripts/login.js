async function autenticar(api) {
    const username = document.getElementById("email").value.trim();
    const password = document.getElementById("senha").value.trim();

    if (!username || !password) { Swal.fire("Campos obrigatórios", "Preencha todos os campos.", "warning"); return; }

    try {
        const resposta = await fetch("https://servidordomal.fun/api/" + api, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) });

        if (resposta.status == 200 || resposta.status == 201) { const raw = await resposta.json(); localStorage.setItem("Mail-Token", raw.response); window.location.href = "/mail"; } 
        else if (resposta.status == 401) { Swal.fire("Erro", "Usuário ou senha incorretos!"); }
        else if (resposta.status == 409) { Swal.fire("Erro", "Este nome de usuário já está em uso!"); }
    } catch (erro) { Swal.fire("Erro", "Erro na conexão com o servidor.", "error"); }
}

window.onload = () => {
    const form = document.querySelector("form");
    const botoes = form.querySelectorAll("button");

    botoes[0].addEventListener("click", function (event) { event.preventDefault(); autenticar("login"); });
    botoes[1].addEventListener("click", function (event) { event.preventDefault(); autenticar("signup"); });
};
