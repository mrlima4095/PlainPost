async function conectar(acao) {
    const username = document.getElementById("email");
    const password = document.getElementById("senha");

    if (!email || !senha) {
        window.location.href = "#"; 
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
            window.location.href = "#"; 
        } 
        else if (dados.response === "1") { alert("Usuário ou senha incorretos!"); } 
        else if (dados.response === "2") { alert("Ocorreu um erro interno!"); } 
        else if (dados.response === "3") { alert("Nome de usuário já está em uso!"); } 
        else if (dados.response === "4") { alert("Destinatario não encontrado!"); } 
        else if (dados.response === "5") { alert("Ocorreu um erro interno!"); } 
        else if (dados.response === "6") { alert("Quantidade invalida de moedas!"); } 
        else if (dados.response === "7") { alert("Saldo insuficiente!"); } 
        else if (dados.response === "8") { alert("A nova senha é invalida!"); }
        

    } catch (erro) {
        alert("Erro na conexão com o servidor.");
        console.error(erro);
    }
}
