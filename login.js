async function autenticar(acao) {
    const email = document.getElementById("email").value.trim();
    const senha = document.getElementById("senha").value.trim();

    if (!email || !senha) {
        alert("Preencha todos os campos.");
        return;
    }

    const payload = {
        username: email,
        password: senha,
        action: acao
    };

    try {
        const resposta = await fetch("http://localhost:10143/badmail", {
            method: "POST",
            headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
        });

        const dados = await resposta.json();

        if (dados.response === "0") {
            localStorage.setItem("username", email);
            localStorage.setItem("password", senha);
            window.location.href = "index.html"; 
        } 
        else if (dados.response === "1") { alert("Usuário ou senha incorretos!"); } 
        else if (dados.response === "3") { alert("Nome de usuário já está em uso!"); }
        else if (dados.response === "9") { alert("Ocorreu um erro interno!"); } 
        else { alert(dados.response); }
        

    } catch (erro) {
        alert("Erro na conexão com o servidor.");
        console.error(erro);
    }
}

window.onload = () => {
    const form = document.querySelector("form");
    const botoes = form.querySelectorAll("button");

    botoes[0].addEventListener("click", function (event) {
        event.preventDefault();
        autenticar("status");
    });

    botoes[1].addEventListener("click", function (event) {
        event.preventDefault();
        autenticar("signup");
    });
};