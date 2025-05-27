<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>PlainPost - Login</title>


    <link rel="stylesheet" href="style.css">
    <link rel="icon" href="favicon.ico" type="image/x-icon" />

    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script type="text/javascript">

        async function autenticar(api) {
            const email = document.getElementById("email").value.trim();
            const senha = document.getElementById("senha").value.trim();

            if (!email || !senha) { Swal.fire("Campos obrigatórios", "Preencha todos os campos.", "warning"); return; }

            const payload = { username: email, password: senha };

            try {
                const resposta = await fetch("https://servidordomal.fun/api/" + api, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });

                if (resposta.status === 200) { 
                    const raw = await resposta.json();

                    localStorage.setItem("Mail-Token", raw.response); 
                    window.location.href = "/mail"; 
                }
                else if (resposta.status === 401) { Swal.fire("Erro", "Usuário ou senha incorretos!"); }
                else if (resposta.status === 409) { Swal.fire("Erro", "Este nome de usuário já esta em uso!"); }
            } catch (erro) { Swal.fire("Erro", "Erro na conexão com o servidor.", "error"); }
        }

        window.onload = () => {
            const form = document.querySelector("form");
            const botoes = form.querySelectorAll("button");

            botoes[0].addEventListener("click", function (event) { event.preventDefault(); autenticar("login"); });
            botoes[1].addEventListener("click", function (event) { event.preventDefault(); autenticar("signup"); });
        };
    </script>


</head>
<body>
    <div id="conteiner">
        <header>
            <h2>PlainPost - Login</h2>
            <p>Não use seu nome real como usuario nem use suas senhas reais aqui!</p>
        </header>
        <form>
            <label for="email">ID:</label><br />
            <input type="user" id="email" name="email" required /><br /><br />

            <label for="senha">Senha:</label><br />
            <input type="password" id="senha" name="senha" required /><br /><br />

            <button type="submit">Entrar</button>
            <button type="submit">Registrar-se</button>
            <br><a href="/mail/privacy">Política de Privacidade</a>
        </form>
    </div>
</body>
</html>
