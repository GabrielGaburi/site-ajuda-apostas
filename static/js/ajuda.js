// Monta o conteúdo do popup sem interpretar os dados como HTML
function montarPopup(nome, cidade, tipo, endereco, telefone, observacao) {

    const conteudo = document.createElement("div");

    const titulo = document.createElement("strong");
    titulo.textContent = nome;
    conteudo.appendChild(titulo);

    [cidade, tipo, "📍 " + endereco, telefone ? "📞 " + telefone : "", observacao || ""].forEach(function (linha) {
        if (!linha) {
            return;
        }

        conteudo.appendChild(document.createElement("br"));
        conteudo.appendChild(document.createTextNode(linha));
    });

    return conteudo;
}

window.irParaLocal = function (
    lat,
    lng,
    nome,
    cidade,
    tipo,
    endereco,
    telefone,
    observacao
) {

    const map = window._leafletMap;

    if (!map) {
        return;
    }

    map.setView([lat, lng], 15);

    L.popup()
        .setLatLng([lat, lng])
        .setContent(montarPopup(nome, cidade, tipo, endereco, telefone, observacao))
        .openOn(map);

    const mapa = document.getElementById("map");

    if (!mapa) {
        return;
    }

    window.scrollTo({
        top: mapa.offsetTop - 100,
        behavior: "smooth"
    });
};


function normalizarTexto(texto) {

    return texto
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");

}


document.addEventListener("DOMContentLoaded", function () {

    const mapElement = document.getElementById("map");

    if (!mapElement) {
        return;
    }


    // ==========================
    // CARREGAR LOCAIS DO FLASK
    // ==========================

    const locaisJson = mapElement.dataset.locais || "[]";

    let locais = [];

    try {

        locais = JSON.parse(locaisJson);

    } catch (error) {

        console.error("Erro ao interpretar os locais:", error);

    }

    // ==========================
    // CRIAR MAPA
    // ==========================

    const map = L.map("map").setView(
        [-23.55052, -46.633308],
        7
    );

    window._leafletMap = map;


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);


    // ==========================
    // ÍCONES
    // ==========================

    const iconeVermelho = new L.Icon({

        iconUrl:
            "/static/img/leaflet/marker-icon-red.png",

        shadowUrl:
            "/static/img/leaflet/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    const iconeAzul = new L.Icon({

        iconUrl:
            "/static/img/leaflet/marker-icon-blue.png",

        shadowUrl:
            "/static/img/leaflet/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    const iconeVerde = new L.Icon({

        iconUrl:
            "/static/img/leaflet/marker-icon-green.png",

        shadowUrl:
            "/static/img/leaflet/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    function escolherIcone(tipo) {

        if (!tipo) {
            return iconeAzul;
        }

        if (tipo.includes("Atendimento") || tipo.includes("CAPS")) {
            return iconeVermelho;
        }

        if (tipo.includes("Hospital")) {
            return iconeAzul;
        }

        if (tipo.includes("Grupo")) {
            return iconeVerde;
        }

        return iconeAzul;

    }


    // ==========================
    // CRIAR MARCADORES
    // ==========================

    const marcadores = [];


    locais.forEach(item => {

        const lat = Number(item.lat);
        const lng = Number(item.lng);


        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {

            console.error(
                "Coordenadas inválidas:",
                item
            );

            return;

        }


        const marcador = L.marker(
            [lat, lng],
            {
                icon: escolherIcone(item.tipo)
            }
        )
            .addTo(map)
            .bindPopup(
                montarPopup(
                    item.nome,
                    item.cidade,
                    item.tipo,
                    item.endereco,
                    item.telefone,
                    item.observacao
                )
            );


        marcadores.push(marcador);

    });




    // ==========================
    // MOSTRAR TODOS OS MARCADORES
    // ==========================

    if (marcadores.length > 0) {

        const grupo =
            L.featureGroup(marcadores);

        map.fitBounds(
            grupo.getBounds(),
            {
                padding: [30, 30]
            }
        );

    }


    
    // ==========================
    // BOTÕES VER NO MAPA
    // ==========================

    document
        .querySelectorAll(".btn-ver-local")
        .forEach(botao => {

            botao.addEventListener(
                "click",
                function () {

                    const lat =
                        Number(this.dataset.lat);

                    const lng =
                        Number(this.dataset.lng);

                    const nome =
                        this.dataset.nome;


                    window.irParaLocal(
                        lat,
                        lng,
                        nome,
                        this.dataset.cidade,
                        this.dataset.tipo,
                        this.dataset.endereco,
                        this.dataset.telefone,
                        this.dataset.observacao
                    );

                }
            );

        });

});