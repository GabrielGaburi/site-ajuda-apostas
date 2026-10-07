document.addEventListener("DOMContentLoaded", function () {

    const cpf = document.getElementById("cpf");
    const telefone = document.getElementById("telefone");
    const erroTelefone = document.getElementById("erroTelefone");
    const cep = document.getElementById("cep");
    const erroCep = document.getElementById("erroCep");
    const sucessoCep = document.getElementById("sucessoCep");
    const dataNascimento = document.getElementById("data_nascimento");
    const erroDataNascimento = document.getElementById("erroDataNascimento");



    // =========================
    // CPF
    // =========================

    if (cpf) {

        cpf.addEventListener("input", function () {

            let valor = this.value.replace(/\D/g, "");

            valor = valor.substring(0, 11);

            if (valor.length > 9) {

                this.value =
                    valor.substring(0, 3) + "." +
                    valor.substring(3, 6) + "." +
                    valor.substring(6, 9) + "-" +
                    valor.substring(9);

            } else if (valor.length > 6) {

                this.value =
                    valor.substring(0, 3) + "." +
                    valor.substring(3, 6) + "." +
                    valor.substring(6);

            } else if (valor.length > 3) {

                this.value =
                    valor.substring(0, 3) + "." +
                    valor.substring(3);

            } else {

                this.value = valor;
            }
            


        });
    }


    // =========================
    // TELEFONE
    // =========================

    if (telefone) {

        telefone.addEventListener("input", function () {

            let valor = this.value.replace(/\D/g, "");

            valor = valor.substring(0, 11);

            if (valor.length > 10) {

                this.value =
                    "(" +
                    valor.substring(0, 2) + ") " +
                    valor.substring(2, 7) + "-" +
                    valor.substring(7);

            } else if (valor.length > 6) {

                this.value =
                    "(" +
                    valor.substring(0, 2) + ") " +
                    valor.substring(2, 6) + "-" +
                    valor.substring(6);

            } else if (valor.length > 2) {

                this.value =
                    "(" +
                    valor.substring(0, 2) + ") " +
                    valor.substring(2);

            } else {

                this.value = valor;
            }

            const quantidadeDigitos = valor.length;

            if (quantidadeDigitos > 0 && quantidadeDigitos < 10) {

                telefone.classList.remove("is-valid");
                telefone.classList.add("is-invalid");

                if (erroTelefone) {
                    erroTelefone.style.display = "block";
                }

            } else if (quantidadeDigitos === 10 || quantidadeDigitos === 11) {

                telefone.classList.remove("is-invalid");
                telefone.classList.add("is-valid");

                if (erroTelefone) {
                    erroTelefone.style.display = "none";
                }

            } else {

                telefone.classList.remove("is-valid", "is-invalid");

                if (erroTelefone) {
                    erroTelefone.style.display = "none";
                }
            }
        });
    }


    // =========================
    // CEP
    // =========================

    if (cep) {

        cep.addEventListener("input", function () {

            let valor = this.value.replace(/\D/g, "");

            valor = valor.substring(0, 8);

            if (valor.length > 5) {

                this.value =
                    valor.substring(0, 5) + "-" +
                    valor.substring(5);

            } else {

                this.value = valor;
            }

            const quantidadeDigitos = valor.length;

            // CEP incompleto
            if (quantidadeDigitos < 8) {

                cep.classList.remove("is-valid", "is-invalid");

                if (erroCep) {
                    erroCep.textContent = "Digite um CEP válido.";
                    erroCep.style.display = "none";
                }

                if (sucessoCep) {
                    sucessoCep.style.display = "none";
                }

                return;
            }

            // CEP com 8 dígitos
            // Agora vamos consultar o ViaCEP

            if (erroCep) {
                erroCep.style.display = "none";
            }

            if (sucessoCep) {
                sucessoCep.style.display = "none";
            }

            fetch(`https://viacep.com.br/ws/${valor}/json/`)
                .then(response => response.json())
                .then(dados => {

                    if (dados.erro) {

                        cep.classList.remove("is-valid");
                        cep.classList.add("is-invalid");

                        if (erroCep) {
                            erroCep.textContent = "CEP não encontrado.";
                            erroCep.style.display = "block";
                        }

                        if (sucessoCep) {
                            sucessoCep.style.display = "none";
                        }

                    } else {

                        cep.classList.remove("is-invalid");
                        cep.classList.add("is-valid");

                        if (erroCep) {
                            erroCep.style.display = "none";
                        }

                        if (sucessoCep) {
                            sucessoCep.style.display = "block";
                        }
                    }

                })
                .catch(erro => {

                    console.error("Erro ao consultar o CEP:", erro);

                });

        });
    }
    // =========================
    // DATA DE NASCIMENTO
    // =========================

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

        // =========================
        // BLOQUEIA ENVIO COM DATA INVÁLIDA
        // =========================

        const formulario = dataNascimento?.closest("form");

        if (formulario) {

            formulario.addEventListener("submit", function (event) {

                if (dataNascimento.classList.contains("is-invalid")) {

                    event.preventDefault();

                    dataNascimento.focus();
                }
            });
        }

});

    

