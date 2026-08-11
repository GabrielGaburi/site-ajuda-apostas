window.toggleSenha = function (campoId, iconeId) {
    const campo = document.getElementById(campoId);
    const icone = document.getElementById(iconeId);

    if (!campo || !icone) {
        return;
    }

    if (campo.type === "password") {
        campo.type = "text";
        icone.classList.remove("bi-eye");
        icone.classList.add("bi-eye-slash");
    } else {
        campo.type = "password";
        icone.classList.remove("bi-eye-slash");
        icone.classList.add("bi-eye");
    }
};

const telefone = document.getElementById("telefone");
if (telefone) {
    telefone.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "");
        valor = valor.replace(/^(\d{2})(\d)/, "($1) $2");
        valor = valor.replace(/(\d{5})(\d)/, "$1-$2");
        this.value = valor;
    });
}

const cep = document.getElementById("cep");
const erroCep = document.getElementById("erroCep");

function buscarCEP() {
    if (!cep) {
        return;
    }

    const valor = cep.value.replace(/\D/g, "");
    if (valor.length !== 8) {
        return;
    }

    cep.classList.remove("is-invalid", "is-valid");
    if (erroCep) {
        erroCep.textContent = "";
    }

    fetch(`https://viacep.com.br/ws/${valor}/json/`)
        .then(res => res.json())
        .then(dados => {
            if (dados.erro) {
                cep.classList.add("is-invalid");
                if (erroCep) {
                    erroCep.textContent = "CEP não encontrado.";
                }
                const rua = document.getElementById("rua");
                const bairro = document.getElementById("bairro");
                const cidade = document.getElementById("cidade");
                const estado = document.getElementById("estado");

                if (rua) rua.value = "";
                if (bairro) bairro.value = "";
                if (cidade) cidade.value = "";
                if (estado) estado.value = "";
                return;
            }

            const rua = document.getElementById("rua");
            const bairro = document.getElementById("bairro");
            const cidade = document.getElementById("cidade");
            const estado = document.getElementById("estado");

            if (rua) rua.value = dados.logradouro || "";
            if (bairro) bairro.value = dados.bairro || "";
            if (cidade) cidade.value = dados.localidade || "";
            if (estado) estado.value = dados.uf || "";

            cep.classList.add("is-valid");
        })
        .catch(() => {
            cep.classList.add("is-invalid");
            if (erroCep) {
                erroCep.textContent = "Erro ao consultar o CEP.";
            }
        });
}

if (cep) {
    cep.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "");
        valor = valor.substring(0, 8);
        if (valor.length > 5) {
            valor = valor.replace(/^(\d{5})(\d)/, "$1-$2");
        }
        this.value = valor;
    });
}

const senha = document.getElementById("senha");
const confirmar = document.getElementById("confirmarSenha");

if (senha) {
    senha.addEventListener("keyup", () => {
        const texto = senha.value;
        const forca = document.getElementById("forcaSenha");
        if (!forca) {
            return;
        }

        let pontos = 0;
        if (texto.length >= 8 && texto.length <= 16) pontos++;
        if (texto.length > 16) {
            forca.innerHTML = "<span class='text-danger'>Máximo de 16 caracteres</span>";
            return;
        }
        if (/[A-Z]/.test(texto)) pontos++;
        if (/[0-9]/.test(texto)) pontos++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(texto)) pontos++;

        if (pontos <= 1) {
            forca.innerHTML = "<span class='text-danger'>Senha fraca</span>";
        } else if (pontos === 2 || pontos === 3) {
            forca.innerHTML = "<span class='text-warning'>Senha média</span>";
        } else {
            forca.innerHTML = "<span class='text-success'>Senha forte</span>";
        }
    });
}

if (confirmar && senha) {
    confirmar.addEventListener("keyup", () => {
        if (confirmar.value.length === 0) {
            return;
        }
        if (confirmar.value === senha.value) {
            confirmar.classList.remove("is-invalid");
            confirmar.classList.add("is-valid");
        } else {
            confirmar.classList.remove("is-valid");
            confirmar.classList.add("is-invalid");
        }
    });
}
