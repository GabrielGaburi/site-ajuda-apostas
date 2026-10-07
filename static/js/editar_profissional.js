
console.log("EDITAR_PROFISSIONAL.JS CARREGADO");

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("formCadastroProfissional");
    const foto = document.getElementById("foto");
    const cpf = document.querySelector('input[name="cpf"]');
    const telefone = document.querySelector('input[name="telefone"]');
    const cep = document.querySelector('input[name="cep"]');
    const erroCep = document.getElementById("erroCep");
    const sucessoCep = document.getElementById("sucessoCep");
    const estado = document.querySelector('input[name="estado"]');
    const cidade = document.querySelector('input[name="cidade"]');
    const rua = document.querySelector('input[name="rua"]');
    const bairro = document.querySelector('input[name="bairro"]');
    const crp = document.getElementById("crp");
    const erroCrp = document.getElementById("erroCrp");
    const ufCrp = document.getElementById("uf_crp");
    const dataNascimento = document.getElementById("data_nascimento");
    const erroDataNascimento = document.getElementById("erroDataNascimento");

    console.log("CAMPOS CEP:", {
        estado,
        cidade,
        rua,
        bairro
    });

    if (!form) {
        return;
    }

    // =====================================================
    // CONTROLA SE O FORMULÁRIO FOI ALTERADO
    // =====================================================

    let formularioAlterado = false;

    form.addEventListener("input", function () {
        formularioAlterado = true;
    });

    form.addEventListener("change", function () {
        formularioAlterado = true;
    });


    // =====================================================
    // PRÉ-VISUALIZAÇÃO DA NOVA FOTO
    // =====================================================

    if (foto) {

        foto.addEventListener("change", function () {

            const arquivo = foto.files[0];

            if (!arquivo) {
                return;
            }

            const extensoesPermitidas = [
                "image/jpeg",
                "image/png"
            ];

            if (!extensoesPermitidas.includes(arquivo.type)) {

                alert("Selecione uma imagem JPG, JPEG ou PNG.");

                foto.value = "";

                return;
            }

            const imagemAtual = document.getElementById("fotoPreview");

            if (!imagemAtual) {
                return;
            }

            const leitor = new FileReader();

            leitor.onload = function (evento) {

                imagemAtual.src = evento.target.result;

            };

            leitor.readAsDataURL(arquivo);

        });

    }

    if (cpf) {

        cpf.addEventListener("input", function () {

            cpf.value = aplicarMascaraCPF(cpf.value);

        });

    }


    if (telefone) {

        telefone.addEventListener("input", function () {

            telefone.value = aplicarMascaraTelefone(telefone.value);

        });

    }


    if (cep) {
        cep.addEventListener("input", function () {
            cep.value = aplicarMascaraCEP(cep.value);

            cep.classList.remove("is-valid", "is-invalid");

            if (erroCep) {
                erroCep.style.display = "none";
            }

            if (sucessoCep) {
                sucessoCep.style.display = "none";
            }

            const cepNumeros = cep.value.replace(/\D/g, "");

            if (cepNumeros.length === 8) {

                fetch(`https://viacep.com.br/ws/${cepNumeros}/json/`)
                    .then(response => response.json())
                    .then(dados => {

                        if (dados.erro) {
                            cep.classList.add("is-invalid");

                            if (erroCep) {
                                erroCep.textContent = "CEP não encontrado.";
                                erroCep.style.display = "block";
                            }

                            return;
                        }

                        // Preenche o endereço automaticamente
                        if (estado) {
                            estado.value = dados.uf;
                        }

                        if (cidade) {
                            cidade.value = dados.localidade;
                        }

                        if (rua) {
                            rua.value = dados.logradouro;
                        }

                        if (bairro) {
                            bairro.value = dados.bairro;
                        }

                        cep.classList.add("is-valid");

                        if (sucessoCep) {
                            sucessoCep.textContent =
                                `CEP válido. Endereço encontrado: ${dados.logradouro}, ${dados.bairro} - ${dados.localidade}/${dados.uf}.`;

                            sucessoCep.style.display = "block";
                        }
                    })
                    .catch(() => {

                        cep.classList.add("is-invalid");

                        if (erroCep) {
                            erroCep.textContent =
                                "Não foi possível consultar o CEP.";

                            erroCep.style.display = "block";
                        }
                    });
            }
        });
    }

    if (dataNascimento) {

        dataNascimento.addEventListener("input", function () {

            let valor = dataNascimento.value.replace(/\D/g, "");

            valor = valor.substring(0, 8);

            if (valor.length > 4) {

                dataNascimento.value =
                    valor.substring(0, 2) + "/" +
                    valor.substring(2, 4) + "/" +
                    valor.substring(4);

            } else if (valor.length > 2) {

                dataNascimento.value =
                    valor.substring(0, 2) + "/" +
                    valor.substring(2);

            } else {

                dataNascimento.value = valor;
            }

            dataNascimento.classList.remove("is-valid", "is-invalid");

            if (erroDataNascimento) {
                erroDataNascimento.style.display = "none";
            }

            if (valor.length === 8) {

                const dia = parseInt(valor.substring(0, 2));
                const mes = parseInt(valor.substring(2, 4));
                const ano = parseInt(valor.substring(4, 8));

                const data = new Date(ano, mes - 1, dia);

                const dataValida =
                    data.getFullYear() === ano &&
                    data.getMonth() === mes - 1 &&
                    data.getDate() === dia;

                const hoje = new Date();

                let idade =
                    hoje.getFullYear() -
                    ano;

                const aniversarioAindaNaoAconteceu =
                    hoje.getMonth() < mes - 1 ||
                    (
                        hoje.getMonth() === mes - 1 &&
                        hoje.getDate() < dia
                    );

                if (aniversarioAindaNaoAconteceu) {
                    idade--;
                }

                if (
                    !dataValida ||
                    data > hoje ||
                    idade < 18 ||
                    idade > 100
                ) {

                    dataNascimento.classList.remove("is-valid");
                    dataNascimento.classList.add("is-invalid");

                    if (erroDataNascimento) {
                        erroDataNascimento.textContent =
                            "Data de nascimento inválida. Informe uma data entre 18 e 100 anos.";

                        erroDataNascimento.style.display = "block";
                    }

                } else {

                    dataNascimento.classList.remove("is-invalid");
                    dataNascimento.classList.add("is-valid");

                    if (erroDataNascimento) {
                        erroDataNascimento.style.display = "none";
                    }
                }
            }
        });
    }

    
    const regioesCRP = {
        "01": "DF",
        "02": "PE",
        "03": "CE",
        "04": "MG",
        "05": "BA",
        "06": "SP",
        "07": "RS",
        "08": "PR",
        "09": "GO",
        "10": "PA/AP",
        "11": "SC",
        "12": "RJ",
        "13": "PB",
        "14": "MS",
        "15": "AL",
        "16": "ES",
        "17": "RN",
        "18": "PI",
        "19": "SE",
        "20": "AM/RR",
        "21": "RO/AC",
        "22": "MA",
        "23": "TO"
    };

    if (crp) {

        crp.addEventListener("input", function () {

            let valor = this.value.replace(/\D/g, "");

            valor = valor.substring(0, 8);

            if (valor.length > 2) {
                valor = valor.replace(/^(\d{2})(\d+)/, "$1/$2");
            }

            this.value = valor;

            const codigo = valor
                .replace(/\D/g, "")
                .substring(0, 2);

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
                            erroCrp.textContent =
                                "Código do CRP inexistente.";

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


    // =====================================================
    // EVITA SAIR DA PÁGINA SEM SALVAR
    // =====================================================

    window.addEventListener("beforeunload", function (evento) {

        if (!formularioAlterado) {
            return;
        }

        evento.preventDefault();
        evento.returnValue = "";

    });


    // =====================================================
    // ENVIO DO FORMULÁRIO
    // =====================================================

    form.addEventListener("submit", function (evento) {

        if (
            dataNascimento &&
            dataNascimento.classList.contains("is-invalid")
        ) {

            evento.preventDefault();

            dataNascimento.focus();

            return;
        }

        formularioAlterado = false;

    });

});
function aplicarMascaraCPF(valor) {

    valor = valor.replace(/\D/g, "");

    valor = valor.substring(0, 11);

    valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
    valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
    valor = valor.replace(/(\d{3})(\d{1,2})$/, "$1-$2");

    return valor;
}


function aplicarMascaraTelefone(valor) {

    valor = valor.replace(/\D/g, "");

    valor = valor.substring(0, 11);

    if (valor.length <= 10) {

        valor = valor.replace(/(\d{2})(\d)/, "($1) $2");
        valor = valor.replace(/(\d{4})(\d)/, "$1-$2");

    } else {

        valor = valor.replace(/(\d{2})(\d)/, "($1) $2");
        valor = valor.replace(/(\d{5})(\d)/, "$1-$2");

    }

    return valor;
}


function aplicarMascaraCEP(valor) {

    valor = valor.replace(/\D/g, "");

    valor = valor.substring(0, 8);

    valor = valor.replace(/(\d{5})(\d)/, "$1-$2");

    return valor;
}
