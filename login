<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>BadMail - Login</title>
    
    <script>
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
                action: acao,
            };

            try {
                const resposta = await fetch("https://servidordomal.fun/api/badmail", {
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
                    window.location.href = "/mail"; 
                } 
                else if (dados.response === "1") { alert("Usuário ou senha incorretos!"); } 
                else if (dados.response === "3") { alert("Nome de usuário já está em uso!"); }
                else if (dados.response === "9") { alert("Ocorreu um erro interno!"); } 
                else { alert(dados.response); }
                

            } catch (erro) {
                alert("Erro na conexão com o servidor.");
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
    </script>
</head>
<body>
    <h2>Login</h2>
    <p>Não use seu nome real como usuario nem use suas senhas reais aqui!</p>
    <form>
        <label for="email">ID:</label><br />
        <input type="user" id="email" name="email" required /><br /><br />

        <label for="senha">Senha:</label><br />
        <input type="password" id="senha" name="senha" required /><br /><br />

        <button type="submit">Entrar</button>
        <button type="submit">Registrar-se</button>
    </form>
</body>
</html>
