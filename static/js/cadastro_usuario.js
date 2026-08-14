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

// Validação e formatação de CPF
const cpf = document.getElementById("cpf");
if (cpf) {
    cpf.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "");
        valor = valor.substring(0, 11);
        valor = valor.replace(/^(\d{3})(\d)/, "$1.$2");
        valor = valor.replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3");
        valor = valor.replace(/\.(\d{3})(\d)/, ".$1-$2");
        this.value = valor;
    });

    cpf.addEventListener("blur", function () {
        const erroCpf = document.getElementById("erroCpf");
        const valor = this.value.replace(/\D/g, "");

        if (valor.length === 11 && validarCPF(valor)) {
            this.classList.remove("is-invalid");
            this.classList.add("is-valid");
            if (erroCpf) erroCpf.textContent = "";
        } else if (valor.length > 0) {
            this.classList.add("is-invalid");
            if (erroCpf) erroCpf.textContent = "CPF inválido.";
        } else {
            this.classList.remove("is-invalid", "is-valid");
            if (erroCpf) erroCpf.textContent = "";
        }
    });
}

// Função para validar CPF
function validarCPF(cpf) {
    if (cpf.length !== 11) return false;

    // Verifica se todos os dígitos são iguais
    if (/^(\d)\1{10}$/.test(cpf)) return false;

    // Calcula primeiro dígito verificador
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(9))) return false;

    // Calcula segundo dígito verificador
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(10))) return false;

    return true;
}

// Validação de data de nascimento
const dataNascimento = document.getElementById("dataNascimento");
if (dataNascimento) {
    dataNascimento.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "");
        if (valor.length >= 2) {
            valor = valor.substring(0, 2) + "/" + valor.substring(2);
        }
        if (valor.length >= 5) {
            valor = valor.substring(0, 5) + "/" + valor.substring(5, 9);
        }
        this.value = valor;
    });

    dataNascimento.addEventListener("blur", function () {
        const erroNascimento = document.getElementById("erroNascimento");
        const valor = this.value;
        const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;

        if (!regex.test(valor) && valor.length > 0) {
            this.classList.add("is-invalid");
            if (erroNascimento) erroNascimento.textContent = "Formato deve ser dd/mm/aaaa.";
        } else if (regex.test(valor)) {
            const [, dia, mes, ano] = valor.match(regex);
            if (!validarData(parseInt(dia), parseInt(mes), parseInt(ano))) {
                this.classList.add("is-invalid");
                if (erroNascimento) erroNascimento.textContent = "Data inválida.";
            } else {
                this.classList.remove("is-invalid");
                this.classList.add("is-valid");
                if (erroNascimento) erroNascimento.textContent = "";
            }
        } else {
            this.classList.remove("is-invalid", "is-valid");
            if (erroNascimento) erroNascimento.textContent = "";
        }
    });
}

// Função para validar data
function validarData(dia, mes, ano) {
    if (mes < 1 || mes > 12) return false;

    const diasPorMes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if ((ano % 4 === 0 && ano % 100 !== 0) || ano % 400 === 0) {
        diasPorMes[1] = 29;
    }

    if (dia < 1 || dia > diasPorMes[mes - 1]) return false;

    const hoje = new Date();
    const dataNasc = new Date(ano, mes - 1, dia);
    if (dataNasc > hoje) return false;

    return true;
}

// Validação de email
const email = document.getElementById("email");
if (email) {
    email.addEventListener("blur", function () {
        const erroEmail = document.getElementById("erroEmail");
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!regex.test(this.value) && this.value.length > 0) {
            this.classList.add("is-invalid");
            if (erroEmail) erroEmail.textContent = "Email inválido.";
        } else if (regex.test(this.value)) {
            this.classList.remove("is-invalid");
            this.classList.add("is-valid");
            if (erroEmail) erroEmail.textContent = "";
        } else {
            this.classList.remove("is-invalid", "is-valid");
            if (erroEmail) erroEmail.textContent = "";
        }
    });
}

// Formatação de telefone
const telefone = document.getElementById("telefone");
if (telefone) {
    telefone.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "");
        valor = valor.replace(/^(\d{2})(\d)/, "($1) $2");
        valor = valor.replace(/(\d{5})(\d)/, "$1-$2");
        this.value = valor;
    });
}

// CEP - Busca e validação
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

// Evento do botão de busca CEP
const btnBuscarCep = document.getElementById("btnBuscarCep");
if (btnBuscarCep) {
    btnBuscarCep.addEventListener("click", buscarCEP);
}

// Formatação de CEP ao digitar
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

// Validação de força de senha
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

// Validação de confirmação de senha
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

