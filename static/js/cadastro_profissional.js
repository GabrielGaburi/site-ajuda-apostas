// O botão de mostrar/ocultar senha é tratado pelo mostrar_senha.js (carregado no base.html)

const formCadastro = document.getElementById("formCadastroProfissional");
const botaoCadastrar = document.getElementById("botaoCadastrar");


// =========================
// MENSAGENS DOS CAMPOS
// =========================

// Cada campo tem um <div id="aviso-<name>"> para as mensagens do JS
function mostrarAviso(campo, texto, valido) {
    const aviso = document.getElementById("aviso-" + campo.name);

    campo.classList.toggle("is-invalid", valido === false);
    campo.classList.toggle("is-valid", valido === true);

    if (valido === false) {
        campo.setAttribute("aria-invalid", "true");
    } else {
        campo.removeAttribute("aria-invalid");
    }

    if (aviso) {
        aviso.textContent = texto || "";
        aviso.classList.toggle("text-danger", valido === false);
        aviso.classList.toggle("text-success", valido === true);
    }
}

function limparAviso(campo) {
    mostrarAviso(campo, "", null);
}

// Remove a mensagem de erro vinda do servidor assim que o usuário mexe no campo
document.querySelectorAll("#formCadastroProfissional [aria-invalid='true']").forEach(campo => {
    const evento = campo.type === "checkbox" || campo.type === "file" || campo.tagName === "SELECT" ? "change" : "input";

    campo.addEventListener(evento, function () {
        campo.classList.remove("is-invalid");
        campo.removeAttribute("aria-invalid");

        const mensagem = document.getElementById("erro-" + campo.name);
        if (mensagem) {
            mensagem.remove();
        }
    }, { once: true });
});


// =========================
// REGRAS DE VALIDAÇÃO
// (as mesmas do servidor, em validar_dados_pessoais e cadastro_profissional no app.py)
// =========================

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

// Retorna a idade, ou null se a data não existir no calendário
function calcularIdade(dia, mes, ano) {
    const data = new Date(ano, mes - 1, dia);

    if (data.getFullYear() !== ano || data.getMonth() !== mes - 1 || data.getDate() !== dia) {
        return null;
    }

    const hoje = new Date();
    let idade = hoje.getFullYear() - ano;

    if (hoje.getMonth() < mes - 1 || (hoje.getMonth() === mes - 1 && hoje.getDate() < dia)) {
        idade--;
    }

    return idade;
}

function faltandoNaSenha(texto) {
    const faltando = [];

    if (texto.length < 8) faltando.push("8 caracteres");
    if (!/[A-Z]/.test(texto)) faltando.push("uma letra maiúscula");
    if (!/[0-9]/.test(texto)) faltando.push("um número");
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(texto)) faltando.push("um caractere especial");

    return faltando;
}

// Região do CRP -> UFs atendidas. Vem do servidor (REGIOES_CRP no app.py)
const ufCrp = document.getElementById("uf_crp");
let regioesCRP = {};
try {
    regioesCRP = JSON.parse(ufCrp?.dataset.regioes || "{}");
} catch (erro) {
    regioesCRP = {};
}

const campoFoto = document.getElementById("foto");
const LIMITE_FOTO_MB = parseInt(campoFoto?.dataset.limiteMb || "5", 10);

// Cada função devolve a mensagem de erro, ou "" se o campo estiver correto
const regras = {

    nome: valor => {
        if (!valor) return "Informe seu nome.";
        if (!/^[\p{L}]+(?:[ '\-][\p{L}]+)*$/u.test(valor)) return "Use apenas letras.";
        return "";
    },

    sobrenome: valor => {
        if (!valor) return "Informe seu sobrenome.";
        if (!/^[\p{L}]+(?:[ '\-][\p{L}]+)*$/u.test(valor)) return "Use apenas letras.";
        return "";
    },

    cpf: valor => {
        const digitos = valor.replace(/\D/g, "");
        if (!digitos) return "Informe seu CPF.";
        if (!validarCPF(digitos)) return "CPF inválido.";
        return "";
    },

    data_de_nascimento: valor => {
        if (!valor) return "Informe sua data de nascimento.";

        const partes = valor.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
        if (!partes) return "Use o formato dd/mm/aaaa.";

        const idade = calcularIdade(parseInt(partes[1]), parseInt(partes[2]), parseInt(partes[3]));
        if (idade === null) return "Data inválida.";
        if (idade < 18 || idade > 100) return "É preciso ter entre 18 e 100 anos.";
        return "";
    },

    sexo: valor => valor ? "" : "Selecione uma opção.",

    email: valor => {
        if (!valor) return "Informe seu e-mail.";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) return "E-mail inválido.";
        return "";
    },

    telefone: valor => {
        const digitos = valor.replace(/\D/g, "");
        if (!digitos) return "Informe seu telefone.";
        if (digitos.length !== 10 && digitos.length !== 11) return "Telefone deve ter DDD e 8 ou 9 dígitos.";
        if (digitos[0] === "0") return "DDD inválido.";
        if (digitos.length === 11 && digitos[2] !== "9") return "Celular deve começar com 9.";
        return "";
    },

    cep: valor => {
        const digitos = valor.replace(/\D/g, "");
        if (!digitos) return "Informe seu CEP.";
        if (digitos.length !== 8) return "CEP deve ter 8 dígitos.";
        return "";
    },

    estado: valor => {
        if (!valor) return "Informe a UF.";
        if (!/^[A-Za-z]{2}$/.test(valor)) return "UF inválida.";
        return "";
    },

    cidade: valor => valor ? "" : "Informe a cidade.",
    rua: valor => valor ? "" : "Informe a rua.",
    numero: valor => valor ? "" : "Informe o número.",
    bairro: valor => valor ? "" : "Informe o bairro.",

    crp: valor => {
        if (!valor) return "Informe o número do CRP.";

        // A região (dois primeiros dígitos) é conferida antes do formato, para avisar logo
        const digitos = valor.replace(/\D/g, "");
        if (digitos.length >= 2 && !regioesCRP[digitos.substring(0, 2)]) return "Região do CRP inexistente.";
        if (!/^\d{2}\/?\d{3,6}$/.test(valor)) return "Use o formato 00/000000.";
        return "";
    },

    uf_crp: valor => valor ? "" : "Selecione a UF do CRP.",

    experiencia: valor => {
        if (valor === "") return "Informe a experiência em anos.";
        if (!/^\d+$/.test(valor) || parseInt(valor, 10) > 60) return "Use um número de 0 a 60.";
        return "";
    },

    especialidade: valor => valor ? "" : "Selecione uma especialidade.",
    faculdade: valor => valor ? "" : "Informe a instituição de ensino.",
    pos: valor => valor ? "" : "Informe a pós-graduação.",

    biografia: valor => {
        if (!valor) return "Escreva uma mini biografia.";
        if (valor.length > 1000) return "A biografia deve ter no máximo 1000 caracteres.";
        return "";
    },

    senha: valor => {
        if (!valor) return "Informe uma senha.";
        if (valor.length > 64) return "A senha deve ter no máximo 64 caracteres.";

        const faltando = faltandoNaSenha(valor);
        if (faltando.length === 0) return "";

        if (faltando.length === 1) return "Precisa de " + faltando[0] + ".";
        return "Precisa de " + faltando.slice(0, -1).join(", ") + " e " + faltando[faltando.length - 1] + ".";
    },

    confirmar_senha: valor => {
        const senha = document.getElementById("senha");
        if (!valor) return "Confirme sua senha.";
        if (senha && valor !== senha.value) return "As senhas não coincidem.";
        return "";
    }
};

// Mensagem positiva exibida quando o campo está correto
const mensagensOk = {
    senha: "✓ Senha válida.",
    confirmar_senha: "✓ As senhas coincidem."
};

// A foto é obrigatória, a não ser que uma foto enviada antes tenha sido mantida
function validarFoto(campo) {
    const arquivo = campo.files && campo.files[0];

    if (!arquivo) {
        if (campo.dataset.fotoMantida) {
            limparAviso(campo);
            return true;
        }
        mostrarAviso(campo, "Selecione uma foto de perfil.", false);
        return false;
    }

    if (!["image/jpeg", "image/png"].includes(arquivo.type)) {
        mostrarAviso(campo, "Use uma imagem JPG ou PNG.", false);
        return false;
    }

    // O limite vale para o envio inteiro; deixa uma folga para o restante do formulário
    if (arquivo.size > LIMITE_FOTO_MB * 1024 * 1024 - 100 * 1024) {
        mostrarAviso(campo, `A foto deve ter no máximo ${LIMITE_FOTO_MB} MB.`, false);
        return false;
    }

    mostrarAviso(campo, "", true);
    return true;
}

// Valida um campo e mostra o resultado; devolve true se estiver correto
function validarCampo(campo) {
    if (campo.type === "checkbox") {
        const ok = campo.checked;
        mostrarAviso(campo, ok ? "" : "Você precisa aceitar os termos para continuar.", ok ? null : false);
        return ok;
    }

    if (campo.type === "file") {
        return validarFoto(campo);
    }

    const regra = regras[campo.name];
    if (!regra) return true;

    // A senha é conferida como foi digitada (o servidor também não remove espaços dela)
    const valor = campo.name === "senha" || campo.name === "confirmar_senha"
        ? campo.value
        : campo.value.trim();

    const erro = regra(valor);

    if (erro) {
        mostrarAviso(campo, erro, false);
        return false;
    }

    mostrarAviso(campo, mensagensOk[campo.name] || "", true);
    return true;
}


// =========================
// MÁSCARAS
// =========================

const cpf = document.getElementById("cpf");
if (cpf) {
    cpf.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "").substring(0, 11);
        valor = valor.replace(/^(\d{3})(\d)/, "$1.$2");
        valor = valor.replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3");
        valor = valor.replace(/\.(\d{3})(\d)/, ".$1-$2");
        this.value = valor;
    });
}

const dataNascimento = document.getElementById("dataNascimento");
if (dataNascimento) {
    dataNascimento.addEventListener("input", function (evento) {
        // Ao apagar, não recoloca a barra (senão o usuário não consegue apagar)
        if (evento.inputType && evento.inputType.startsWith("delete")) {
            return;
        }

        let valor = this.value.replace(/\D/g, "").substring(0, 8);
        if (valor.length >= 5) {
            valor = valor.substring(0, 2) + "/" + valor.substring(2, 4) + "/" + valor.substring(4);
        } else if (valor.length >= 3) {
            valor = valor.substring(0, 2) + "/" + valor.substring(2);
        }
        this.value = valor;
    });
}

// Fixo: (00) 0000-0000 | Celular: (00) 00000-0000
const telefone = document.getElementById("telefone");
if (telefone) {
    telefone.addEventListener("input", function (evento) {
        if (evento.inputType && evento.inputType.startsWith("delete")) {
            return;
        }

        const digitos = this.value.replace(/\D/g, "").substring(0, 11);
        let valor = digitos;

        if (digitos.length > 10) {
            valor = digitos.replace(/^(\d{2})(\d{5})(\d{0,4})$/, "($1) $2-$3");
        } else if (digitos.length > 6) {
            valor = digitos.replace(/^(\d{2})(\d{4})(\d{0,4})$/, "($1) $2-$3");
        } else if (digitos.length > 2) {
            valor = digitos.replace(/^(\d{2})(\d{0,5})$/, "($1) $2");
        }

        this.value = valor;
    });
}

const estado = document.getElementById("estado");
if (estado) {
    estado.addEventListener("input", function () {
        this.value = this.value.replace(/[^A-Za-z]/g, "").toUpperCase();
    });
}


// =========================
// CRP E UF DO CRP
// =========================

// Monta as opções de UF da região; regiões com uma UF só já vêm selecionadas
function atualizarUfCrp(codigo) {
    if (!ufCrp) return;

    const ufs = regioesCRP[codigo] || [];
    const atual = ufCrp.value;

    ufCrp.innerHTML = "";
    ufCrp.add(new Option(ufs.length ? "Selecione" : "Digite o CRP", ""));
    ufs.forEach(uf => ufCrp.add(new Option(uf, uf)));

    if (ufs.length === 1) {
        ufCrp.value = ufs[0];
    } else if (ufs.includes(atual)) {
        ufCrp.value = atual;
    }

    if (ufCrp.value) limparAviso(ufCrp);
}

const crp = document.getElementById("crp");
if (crp) {
    crp.addEventListener("input", function (evento) {
        if (!(evento.inputType && evento.inputType.startsWith("delete"))) {
            let valor = this.value.replace(/\D/g, "").substring(0, 8);
            if (valor.length > 2) {
                valor = valor.replace(/^(\d{2})(\d+)/, "$1/$2");
            }
            this.value = valor;
        }

        const codigo = this.value.replace(/\D/g, "").substring(0, 2);
        atualizarUfCrp(codigo.length === 2 ? codigo : "");

        // Avisa logo se a região não existir
        if (codigo.length === 2 && !regioesCRP[codigo]) {
            mostrarAviso(crp, "Região do CRP inexistente.", false);
        }
    });
}


// =========================
// BIOGRAFIA (CONTADOR)
// =========================

const biografia = document.getElementById("biografia");
const contadorBiografia = document.getElementById("contadorBiografia");

function atualizarContador() {
    if (!biografia || !contadorBiografia) return;

    const restantes = 1000 - biografia.value.length;
    contadorBiografia.textContent = `${biografia.value.length}/1000 caracteres. Aparece no seu perfil público.`;
    contadorBiografia.classList.toggle("text-danger", restantes < 0);
}

if (biografia) {
    biografia.addEventListener("input", atualizarContador);
    atualizarContador();
}


// =========================
// FOTO (PRÉVIA)
// =========================

const previaFoto = document.getElementById("previaFoto");
let urlPrevia = null;

if (campoFoto) {
    campoFoto.addEventListener("change", function () {
        if (urlPrevia) {
            URL.revokeObjectURL(urlPrevia);
            urlPrevia = null;
        }

        const valido = validarFoto(campoFoto);
        const arquivo = campoFoto.files && campoFoto.files[0];

        if (previaFoto) {
            if (valido && arquivo) {
                urlPrevia = URL.createObjectURL(arquivo);
                previaFoto.src = urlPrevia;
                previaFoto.classList.remove("d-none");
            } else {
                previaFoto.removeAttribute("src");
                previaFoto.classList.add("d-none");
            }
        }
    });
}


// =========================
// CEP - BUSCA NO VIACEP
// =========================

const cep = document.getElementById("cep");
const btnBuscarCep = document.getElementById("btnBuscarCep");
const camposEndereco = ["rua", "bairro", "cidade", "estado"];
let ultimoCepBuscado = "";

// Campos preenchidos pelo ViaCEP ficam travados; os vazios são liberados
// para o usuário digitar (CEP único da cidade, CEP não encontrado ou falha na busca)
function ajustarCamposEndereco(liberarTodos) {
    camposEndereco.forEach(id => {
        const campo = document.getElementById(id);
        if (campo) {
            campo.readOnly = !liberarTodos && campo.value.trim() !== "";
        }
    });
}

function preencherEndereco(dados) {
    const valores = {
        rua: dados.logradouro,
        bairro: dados.bairro,
        cidade: dados.localidade,
        estado: dados.uf
    };

    camposEndereco.forEach(id => {
        const campo = document.getElementById(id);
        if (campo) {
            campo.value = valores[id] || "";
            limparAviso(campo);
        }
    });
}

function carregandoCep(ativo) {
    if (!btnBuscarCep) return;

    btnBuscarCep.disabled = ativo;
    btnBuscarCep.innerHTML = ativo
        ? '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>'
        : '<i class="bi bi-search" aria-hidden="true"></i>';
    btnBuscarCep.setAttribute("aria-label", ativo ? "Buscando CEP" : "Buscar endereço pelo CEP");
}

function buscarCEP(forcar) {
    if (!cep) {
        return;
    }

    const valor = cep.value.replace(/\D/g, "");

    // CEP incompleto não apaga o endereço já preenchido
    if (valor.length !== 8) {
        if (forcar) validarCampo(cep);
        return;
    }

    // Evita buscar de novo o mesmo CEP ao sair do campo
    if (!forcar && valor === ultimoCepBuscado) {
        return;
    }

    ultimoCepBuscado = valor;
    limparAviso(cep);
    carregandoCep(true);

    fetch(`https://viacep.com.br/ws/${valor}/json/`)
        .then(res => {
            if (!res.ok) {
                throw new Error("Falha na consulta do CEP");
            }
            return res.json();
        })
        .then(dados => {
            if (dados.erro) {
                mostrarAviso(cep, "CEP não encontrado. Preencha o endereço manualmente.", false);
                preencherEndereco({});
                ajustarCamposEndereco(true);
                return;
            }

            preencherEndereco(dados);
            ajustarCamposEndereco(false);
            mostrarAviso(cep, "", true);

            // Leva o usuário direto para o próximo campo a preencher
            const proximo = ["rua", "bairro"].map(id => document.getElementById(id)).find(c => c && !c.value);
            const numero = document.getElementById("numero");
            (proximo || numero)?.focus();
        })
        .catch(() => {
            ultimoCepBuscado = "";
            mostrarAviso(cep, "Não foi possível consultar o CEP. Preencha o endereço manualmente.", false);
            ajustarCamposEndereco(true);
        })
        .finally(() => carregandoCep(false));
}

if (btnBuscarCep) {
    btnBuscarCep.addEventListener("click", () => buscarCEP(true));
}

if (cep) {
    cep.addEventListener("input", function () {
        let valor = this.value.replace(/\D/g, "").substring(0, 8);
        if (valor.length > 5) {
            valor = valor.replace(/^(\d{5})(\d)/, "$1-$2");
        }
        this.value = valor;

        // Busca sozinho quando o CEP fica completo
        if (valor.replace(/\D/g, "").length === 8) {
            buscarCEP(false);
        }
    });

    cep.addEventListener("blur", () => buscarCEP(false));

    // Ao voltar com erro do servidor, libera os campos de endereço que ficaram vazios
    if (cep.value.replace(/\D/g, "").length === 8) {
        ultimoCepBuscado = cep.value.replace(/\D/g, "");
        ajustarCamposEndereco(false);
    }
}


// =========================
// VALIDAÇÃO AO DIGITAR / SAIR DO CAMPO
// =========================

if (formCadastro) {

    const campos = Array.from(formCadastro.querySelectorAll("input, select, textarea"))
        .filter(campo => campo.type !== "hidden" && campo.name);

    campos.forEach(campo => {

        // Valida ao sair do campo (o CEP é validado pela busca e a foto ao ser escolhida)
        if (campo.name !== "cep" && campo.type !== "file") {
            campo.addEventListener(campo.type === "checkbox" || campo.tagName === "SELECT" ? "change" : "blur", () => {
                if (campo.value || campo.type === "checkbox") validarCampo(campo);
            });
        }

        // Se o campo já está marcado com erro, revalida enquanto o usuário corrige
        if (campo.type !== "file") {
            campo.addEventListener("input", () => {
                if (campo.classList.contains("is-invalid")) validarCampo(campo);
            });
        }
    });

    // Senha e confirmação: mostram o resultado enquanto digita
    const senha = document.getElementById("senha");
    const confirmar = document.getElementById("confirmarSenha");

    if (senha) {
        senha.addEventListener("input", () => {
            if (senha.value) {
                validarCampo(senha);
            } else {
                limparAviso(senha);
            }

            // A confirmação precisa ser conferida de novo quando a senha muda
            if (confirmar && confirmar.value) validarCampo(confirmar);
        });
    }

    if (confirmar) {
        confirmar.addEventListener("input", () => {
            if (confirmar.value) {
                validarCampo(confirmar);
            } else {
                limparAviso(confirmar);
            }
        });
    }


    // =========================
    // ENVIO DO FORMULÁRIO
    // =========================

    formCadastro.addEventListener("submit", function (evento) {

        const invalidos = campos.filter(campo => !validarCampo(campo));

        if (invalidos.length > 0) {
            evento.preventDefault();

            // Se o erro está num campo travado, libera para o usuário corrigir
            invalidos.forEach(campo => {
                if (campo.readOnly) campo.readOnly = false;
            });

            invalidos[0].focus();
            return;
        }

        // Evita envio duplo (o envio leva a foto e pode demorar)
        if (botaoCadastrar) {
            botaoCadastrar.disabled = true;
            botaoCadastrar.textContent = "Enviando...";
        }
    });

    // Reativa o botão se a página voltar pelo botão "voltar" do navegador
    window.addEventListener("pageshow", function () {
        if (botaoCadastrar) {
            botaoCadastrar.disabled = false;
            botaoCadastrar.textContent = "Solicitar Cadastro";
        }
    });
}
