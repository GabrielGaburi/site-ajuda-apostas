window.irParaLocal = function (
    lat,
    lng,
    nome,
    cidade,
    tipo,
    endereco,
    telefone
) {

    const map = window._leafletMap;

    if (!map) {
        return;
    }

    map.setView([lat, lng], 15);

    L.popup()
        .setLatLng([lat, lng])
        .setContent(`
            <strong>${nome}</strong><br>
            ${cidade}<br>
            ${tipo}<br>
            📍 ${endereco}<br>
            📞 ${telefone}
        `)
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

        console.log("Locais carregados:", locais);

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
            "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",

        shadowUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    const iconeAzul = new L.Icon({

        iconUrl:
            "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",

        shadowUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    const iconeVerde = new L.Icon({

        iconUrl:
            "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",

        shadowUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],

        popupAnchor: [1, -34],

        shadowSize: [41, 41]

    });


    function escolherIcone(tipo) {

        if (!tipo) {
            return iconeAzul;
        }

        if (tipo.includes("Atendimento")) {
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
            .bindPopup(`

                <strong>${item.nome}</strong><br>

                ${item.cidade}<br>

                ${item.tipo}<br>

                📍 ${item.endereco}<br>

                📞 ${item.telefone}

            `);


        marcadores.push(marcador);

    });


    console.log(
        "Marcadores criados:",
        marcadores.length
    );


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
                        this.dataset.telefone
                    );

                }
            );

        });

});