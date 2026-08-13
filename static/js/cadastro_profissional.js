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

function validarCpf(cpf) {
    cpf = cpf.replace(/\D/g, "");
    if (cpf.length !== 11) return false;
    if (/^(\d)\1+$/.test(cpf)) return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i), 10) * (10 - i);
    }

    let resto = (soma * 10) % 11;
    if (resto === 10) resto = 0;
    if (resto !== parseInt(cpf.charAt(9), 10)) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i), 10) * (11 - i);
    }

    resto = (soma * 10) % 11;
    if (resto === 10) resto = 0;
    if (resto !== parseInt(cpf.charAt(10), 10)) return false;

    return true;
}

function validarDataNascimento() {
    const dataNascimento = document.getElementById("dataNascimento");
    const erroNascimento = document.getElementById("erroNascimento");

    if (!dataNascimento || !erroNascimento) {
        return true;
    }

    const valor = dataNascimento.value.trim();
    if (!valor) {
        invalido("Data de nascimento obrigatória.");
        return false;
    }

    const partes = valor.split("/");
    if (partes.length !== 3) {
        invalido("Formato inválido.");
        return false;
    }

    const dia = parseInt(partes[0], 10);
    const mes = parseInt(partes[1], 10);
    const ano = parseInt(partes[2], 10);

    if ([dia, mes, ano].some((valor) => Number.isNaN(valor))) {
        invalido("Formato inválido.");
        return false;
    }

    if (mes < 1 || mes > 12) {
        invalido("Mês inválido.");
        return false;
    }

    const dataInformada = new Date(ano, mes - 1, dia);
    const hoje = new Date();
    const diasMes = [31, (ano % 4 === 0 && (ano % 100 !== 0 || ano % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    if (dia < 1 || dia > diasMes[mes - 1]) {
        invalido("Dia inválido.");
        return false;
    }

    if (
        dataInformada.getFullYear() !== ano ||
        dataInformada.getMonth() !== mes - 1 ||
        dataInformada.getDate() !== dia
    ) {
        invalido("Data de nascimento inválida.");
        return false;
    }

    let idade = hoje.getFullYear() - dataInformada.getFullYear();
    const mesAtual = hoje.getMonth() - dataInformada.getMonth();
    const diaAtual = hoje.getDate() - dataInformada.getDate();

    if (mesAtual < 0 || (mesAtual === 0 && diaAtual < 0)) {
        idade -= 1;
    }

    if (idade < 18 || idade > 100) {
        invalido("Idade deve estar entre 18 e 100 anos.");
        return false;
    }

    valido();
    return true;
}

function invalido(msg) {
    const dataNascimento = document.getElementById("dataNascimento");
    const erroNascimento = document.getElementById("erroNascimento");

    if (!dataNascimento || !erroNascimento) {
        return;
    }

    dataNascimento.classList.remove("is-valid");
    dataNascimento.classList.add("is-invalid");
    erroNascimento.textContent = msg;
}

function valido() {
    const dataNascimento = document.getElementById("dataNascimento");
    const erroNascimento = document.getElementById("erroNascimento");

    if (!dataNascimento || !erroNascimento) {
        return;
    }

    dataNascimento.classList.remove("is-invalid");
    dataNascimento.classList.add("is-valid");
}

function buscarCEP() {
    const cep = document.getElementById("cep");
    const erroCep = document.getElementById("erroCep");

    if (!cep || !erroCep) {
        return;
    }

    const valor = cep.value.replace(/\D/g, "");
    if (valor.length !== 8) {
        limparEndereco();
        erroCep.textContent = "Digite um CEP válido.";
        cep.classList.remove("is-valid");
        cep.classList.add("is-invalid");
        return;
    }

    cep.classList.remove("is-invalid", "is-valid");
    erroCep.textContent = "";

    fetch(`https://viacep.com.br/ws/${valor}/json/`)
        .then(response => response.json())
        .then(dados => {
            if (dados.erro) {
                limparEndereco();
                erroCep.textContent = "CEP não encontrado.";
                erroCep.style.display = "block";
                cep.classList.remove("is-valid");
                cep.classList.add("is-invalid");
                return;
            }
            const estado = document.getElementById("estado");
            const cidade = document.getElementById("cidade");
            const rua = document.getElementById("rua");
            const bairro = document.getElementById("bairro");

            if (estado) estado.value = dados.uf || "";
            if (cidade) cidade.value = dados.localidade || "";
            if (rua) rua.value = dados.logradouro || "";
            if (bairro) bairro.value = dados.bairro || "";

            erroCep.textContent = "";
            erroCep.style.display = "none";
            cep.classList.remove("is-invalid");
            cep.classList.add("is-valid");
        });
}

function limparEndereco() {
    const estado = document.getElementById("estado");
    const cidade = document.getElementById("cidade");
    const rua = document.getElementById("rua");
    const bairro = document.getElementById("bairro");

    if (estado) estado.value = "";
    if (cidade) cidade.value = "";
    if (rua) rua.value = "";
    if (bairro) bairro.value = "";
}

function normalizarTexto(texto) {
    return texto
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

(function () {

    const formulario = document.getElementById("formCadastroProfissional");
    const dataNascimento = document.getElementById("dataNascimento");
    const telefone = document.getElementById("telefone");

    if (telefone) {
        telefone.addEventListener("input", function () {
            let valor = this.value.replace(/\D/g, "");
            valor = valor.replace(/^(\d{2})(\d)/, "($1) $2");
            valor = valor.replace(/(\d{5})(\d)/, "$1-$2");
            this.value = valor;
        });
    }

    const cpf = document.getElementById("cpf");
    const erroCpf = document.getElementById("erroCpf");
    if (cpf) {
        cpf.addEventListener("input", function () {
            let valor = this.value.replace(/\D/g, "");
            valor = valor.substring(0, 11);
            valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
            valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
            valor = valor.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
            this.value = valor;

            const numeros = valor.replace(/\D/g, "");
            cpf.classList.remove("is-valid", "is-invalid");
            if (numeros.length === 0) {
                cpf.classList.add("is-invalid");
                if (erroCpf) erroCpf.textContent = "O CPF é obrigatório.";
            } else if (numeros.length === 11) {
                if (validarCpf(valor)) {
                    cpf.classList.add("is-valid");
                } else {
                    cpf.classList.add("is-invalid");
                    if (erroCpf) erroCpf.textContent = "CPF inválido.";
                }
            }
        });
    }

    const crp = document.getElementById("crp");
    const erroCrp = document.getElementById("erroCrp");
    const ufCrp = document.getElementById("uf_crp");
    const regioesCRP = {
        "01": "DF", "02": "PE", "03": "CE", "04": "MG", "05": "BA", "06": "SP", "07": "RS", "08": "PR", "09": "GO", "10": "PA/AP", "11": "SC", "12": "RJ", "13": "PB", "14": "MS", "15": "AL", "16": "ES", "17": "RN", "18": "PI", "19": "SE", "20": "AM/RR", "21": "RO/AC", "22": "MA", "23": "TO"
    };

    if (crp) {
        crp.addEventListener("input", function () {
            let valor = this.value.replace(/\D/g, "");
            valor = valor.substring(0, 8);
            if (valor.length > 2) {
                valor = valor.replace(/^(\d{2})(\d+)/, "$1/$2");
            }
            this.value = valor;

            const codigo = valor.replace(/\D/g, "").substring(0, 2);
            crp.classList.remove("is-valid", "is-invalid");
            if (erroCrp) {
                erroCrp.classList.add("d-none");
            }

            if (ufCrp) {
                if (codigo.length === 2) {
                    if (regioesCRP[codigo]) {
                        ufCrp.value = regioesCRP[codigo];
                    } else {
                        ufCrp.value = "";
                        crp.classList.add("is-invalid");
                        if (erroCrp) {
                            erroCrp.textContent = "Código do CRP inexistente.";
                            erroCrp.classList.remove("d-none");
                        }
                        return;
                    }
                } else {
                    ufCrp.value = "";
                }
            }
            if (valor.length === 9) {
                crp.classList.add("is-valid");
            }
        });
    }

    const senha = document.getElementById("senha");
    const confirmar = document.getElementById("confirmarSenha");

    if (senha) {
        senha.addEventListener("keyup", function () {
            const texto = this.value;
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
        confirmar.addEventListener("keyup", function () {
            if (this.value.length === 0) {
                return;
            }
            if (this.value === senha.value) {
                this.classList.remove("is-invalid");
                this.classList.add("is-valid");
            } else {
                this.classList.remove("is-valid");
                this.classList.add("is-invalid");
            }
        });
    }

    if (formulario) {
        formulario.noValidate = true;

        formulario.addEventListener("submit", function (event) {
            let formularioValido = true;

            if (cpf && !validarCpf(cpf.value.replace(/\D/g, ""))) {
                cpf.classList.add("is-invalid");
                if (erroCpf) {
                    erroCpf.textContent = "CPF inválido.";
                }
                cpf.focus();
                formularioValido = false;
            }

            const email = document.getElementById("email");
            const erroEmail = document.getElementById("erroEmail");
            if (email) {
                const emailValor = email.value.trim();
                const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!regexEmail.test(emailValor)) {
                    email.classList.add("is-invalid");
                    if (erroEmail) {
                        erroEmail.textContent = "Digite um e-mail válido.";
                    }
                    email.focus();
                    formularioValido = false;
                }
            }

            if (dataNascimento && !validarDataNascimento()) {
                dataNascimento.focus();
                formularioValido = false;
            }

            const termos = document.getElementById("termos");
            if (termos && !termos.checked) {
                termos.classList.add("is-invalid");
                termos.focus();
                formularioValido = false;
            }

            if (confirmar && senha) {
                if (confirmar.value !== senha.value || !confirmar.value) {
                    confirmar.classList.remove("is-valid");
                    confirmar.classList.add("is-invalid");
                    formularioValido = false;
                }
            }

            if (!formularioValido) {
                event.preventDefault();
                return false;
            }
        });
    }

    if (dataNascimento) {
        dataNascimento.addEventListener("input", function () {
            let valor = this.value.replace(/\D/g, "");
            valor = valor.substring(0, 8);

            if (valor.length >= 3) {
                valor = valor.substring(0, 2) + "/" + valor.substring(2);
            }

            if (valor.length >= 6) {
                valor = valor.substring(0, 5) + "/" + valor.substring(5);
            }

            this.value = valor;
            this.classList.remove("is-valid", "is-invalid");

            if (valor.length === 10) {
                validarDataNascimento();
            }
        });
    }

    const emailInput = document.getElementById("email");
    const erroEmailInput = document.getElementById("erroEmail");
    if (emailInput) {
        emailInput.addEventListener("input", function () {
            const valor = this.value.trim();
            this.classList.remove("is-valid", "is-invalid");
            if (erroEmailInput) {
                erroEmailInput.textContent = "";
            }
            if (valor.length === 0) {
                this.classList.add("is-invalid");
                if (erroEmailInput) {
                    erroEmailInput.textContent = "O e-mail é obrigatório.";
                }
                return;
            }
            const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (regex.test(valor)) {
                this.classList.add("is-valid");
            } else {
                this.classList.add("is-invalid");
                if (erroEmailInput) {
                    erroEmailInput.textContent = "Digite um e-mail válido.";
                }
            }
        });
    }

    const cepInput = document.getElementById("cep");
    const btnBuscarCep = document.getElementById("btnBuscarCep");
    if (cepInput) {
        cepInput.addEventListener("input", function () {
            let valor = this.value.replace(/\D/g, "");
            valor = valor.substring(0, 8);
            if (valor.length > 5) {
                valor = valor.replace(/^(\d{5})(\d)/, "$1-$2");
            }
            this.value = valor;
        });
    }

    if (btnBuscarCep) {
        btnBuscarCep.addEventListener("click", buscarCEP);
    }
})();
