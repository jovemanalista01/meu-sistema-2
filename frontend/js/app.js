/**
 * LogiScale Web - Lógica Principal da Aplicação Frontend
 * Suporte completo a múltiplos usuários, controle RBAC e responsividade.
 */

document.addEventListener("DOMContentLoaded", () => {
    inicializarNavegacao();
    inicializarEventosMobile();
    inicializarAuthUI();
    carregarDadosIniciais();
});

let abaAtual = "dashboard";
let escalasData = [];
let filtroEscalas = "ativas";

// ============================================================
// NAVEGAÇÃO ENTRE ABAS E RESPONSIVIDADE
// ============================================================
function inicializarNavegacao() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            mudarAba(targetTab);
            fecharSidebarMobile();
        });
    });
}

function inicializarEventosMobile() {
    const btnToggle = document.getElementById("btn-menu-toggle");
    const overlay = document.getElementById("sidebar-overlay");
    const sidebar = document.getElementById("sidebar");

    if (btnToggle) {
        btnToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            overlay.classList.toggle("active");
        });
    }

    if (overlay) {
        overlay.addEventListener("click", fecharSidebarMobile);
    }
}

function fecharSidebarMobile() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (sidebar) sidebar.classList.remove("open");
    if (overlay) overlay.classList.remove("active");
}

function mudarAba(nomeAba) {
    abaAtual = nomeAba;

    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-tab") === nomeAba);
    });

    document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.toggle("active", content.id === `tab-${nomeAba}`);
    });

    const titulos = {
        "dashboard": { title: "Painel & Indicadores", subtitle: "Visão consolidada em tempo real da operação e frota" },
        "escalas": { title: "Escalas de Viagem", subtitle: "Acompanhamento de rotas em andamento, concluídas e trocas" },
        "colaboradores": { title: "Gestão de Colaboradores", subtitle: "Cadastro e controle de motoristas, ajudantes e reservas" },
        "frota": { title: "Frota Pesada", subtitle: "Controle de veículos, placas e histórico operacional" },
        "rotas": { title: "Rotas Operacionais", subtitle: "Destinos cadastrados e previsão de viagem" },
        "afastamentos": { title: "Afastamentos & Licenças", subtitle: "Controle de ausências, atestados e retornos" },
        "historico": { title: "Trilha de Auditoria", subtitle: "Rastreabilidade e log de alterações operacionais" }
    };

    if (titulos[nomeAba]) {
        document.getElementById("page-title").textContent = titulos[nomeAba].title;
        document.getElementById("page-subtitle").textContent = titulos[nomeAba].subtitle;
    }

    recarregarDadosAba(nomeAba);
}

function recarregarDadosAtuais() {
    recarregarDadosAba(abaAtual);
    carregarIndicadores();
    mostrarToast("Dados sincronizados com o servidor!", "success");
}

function recarregarDadosAba(nomeAba) {
    switch (nomeAba) {
        case "dashboard": carregarIndicadores(); break;
        case "escalas": carregarEscalas(); break;
        case "colaboradores": carregarColaboradores(); break;
        case "frota": carregarFrota(); break;
        case "rotas": carregarRotas(); break;
        case "afastamentos": carregarAfastamentos(); break;
        case "historico": carregarHistorico(); break;
    }
}

function carregarDadosIniciais() {
    carregarIndicadores();
    carregarEscalas();
    carregarColaboradores();
    carregarFrota();
    carregarRotas();
    carregarAfastamentos();
    carregarHistorico();
}

// ============================================================
// 1. DASHBOARD & INDICADORES
// ============================================================
async function carregarIndicadores() {
    try {
        const data = await window.api.get("/api/indicadores");

        document.getElementById("kpi-escalas-em-rota").textContent = data.escalas_em_rota || 0;
        document.getElementById("kpi-motoristas-disponiveis").textContent = data.motoristas_disponiveis || 0;
        document.getElementById("kpi-ajudantes-disponiveis").textContent = data.ajudantes_disponiveis || 0;
        document.getElementById("kpi-colaboradores-afastados").textContent = data.colaboradores_afastados || 0;
        document.getElementById("kpi-pontualidade").textContent = `${data.taxa_pontualidade}%`;
        document.getElementById("kpi-frotas-disponiveis").textContent = data.frotas_disponiveis || 0;
        document.getElementById("kpi-reservas").textContent = data.total_reservas || 0;
        document.getElementById("kpi-transbordos").textContent = data.total_transbordos || 0;

        // Top Motoristas
        const topMotList = document.getElementById("list-top-motoristas");
        if (data.top_motoristas && data.top_motoristas.length > 0) {
            topMotList.innerHTML = data.top_motoristas.map((m, idx) => `
                <li class="rank-item">
                    <div class="rank-info">
                        <span class="rank-num">#${idx + 1}</span>
                        <strong>${m.nome}</strong>
                    </div>
                    <span class="rank-badge">${m.total_viagens} viagem(ns)</span>
                </li>
            `).join("");
        } else {
            topMotList.innerHTML = '<li class="rank-item">Nenhum dado registrado</li>';
        }

        // Top Rotas
        const topRotasList = document.getElementById("list-top-rotas");
        if (data.top_rotas && data.top_rotas.length > 0) {
            topRotasList.innerHTML = data.top_rotas.map((r, idx) => `
                <li class="rank-item">
                    <div class="rank-info">
                        <span class="rank-num">#${idx + 1}</span>
                        <strong>${r.nome_rota}</strong>
                    </div>
                    <span class="rank-badge">${r.total_escalas} escala(s)</span>
                </li>
            `).join("");
        } else {
            topRotasList.innerHTML = '<li class="rank-item">Nenhuma rota registrada</li>';
        }

        // Frotas Livres
        carregarFrotasLivresDashboard();
    } catch (err) {
        console.error("Erro ao carregar indicadores:", err);
    }
}

async function carregarFrotasLivresDashboard() {
    try {
        const frotas = await window.api.get("/api/frotas/disponiveis");
        const list = document.getElementById("list-frotas-disponiveis");
        if (!list) return;

        if (frotas.length === 0) {
            list.innerHTML = '<li class="rank-item"><span class="rank-info">Todas as frotas em trânsito</span></li>';
            return;
        }

        list.innerHTML = frotas.map((f, i) => `
            <li class="rank-item">
                <div class="rank-info">
                    <span class="rank-num">${i + 1}</span>
                    <div>
                        <strong>Frota ${f.numero_frota}</strong>
                        <span style="color: var(--text-muted); font-size: 0.8rem;"> — ${f.placa}</span>
                    </div>
                </div>
                <span class="badge badge-livre">Livre</span>
            </li>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar frotas disponíveis:", err);
    }
}

// ============================================================
// 2. ESCALAS & OPERAÇÕES
// ============================================================
function setFiltroEscalas(filtro) {
    filtroEscalas = filtro;
    document.querySelectorAll("#filtro-escalas-tabs .filter-tab").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-filtro") === filtro);
    });
    renderizarEscalas();
}

async function carregarEscalas() {
    try {
        escalasData = await window.api.get("/api/escalas");
        renderizarEscalas();
    } catch (err) {
        console.error("Erro ao carregar escalas:", err);
    }
}

function renderizarEscalas() {
    const tbody = document.querySelector("#tabela-escalas tbody");
    if (!tbody) return;

    let filtradas = escalasData;
    if (filtroEscalas === "ativas") {
        filtradas = escalasData.filter(e => e.status === "em_rota");
    } else if (filtroEscalas === "concluidas") {
        filtradas = escalasData.filter(e => e.status === "chegou");
    }

    if (filtradas.length === 0) {
        const msg = filtroEscalas === "ativas" ? "Nenhuma escala ativa em trânsito." :
                    filtroEscalas === "concluidas" ? "Nenhuma escala concluída encontrada." :
                    "Nenhuma escala cadastrada.";
        tbody.innerHTML = `<tr><td colspan="9" class="text-center">${msg}</td></tr>`;
        return;
    }

    tbody.innerHTML = filtradas.map(e => {
        const isSubstituido = e.status === "substituido";
        const rowClass = isSubstituido ? "row-substituido" : "";

        let statusHtml;
        if (isSubstituido) {
            statusHtml = '<span class="badge-subst" title="Escala com substituição">Subst.</span>';
        } else {
            const badgeClass = `badge badge-${e.status}`;
            const texto = e.status === "em_rota" ? "Em Rota" : "Chegou";
            statusHtml = `<span class="${badgeClass}">${texto}</span>`;
        }

        let acoes = "-";
        if (e.status === "em_rota") {
            acoes = `
                <div class="actions-cell">
                    <button class="btn btn-success btn-sm" onclick="abrirModalChegada(${e.id})" title="Registrar Chegada">
                        <i class="fa-solid fa-flag-checkered"></i> Chegada
                    </button>
                    <div class="actions-dropdown">
                        <button class="actions-toggle" onclick="toggleActionsMenu(this, event)" title="Substituição">
                            <i class="fa-solid fa-repeat"></i>
                        </button>
                        <div class="actions-menu">
                            <button class="actions-menu-item" onclick="fecharActionsMenu(); abrirModalTroca(${e.id}, 'motorista')">
                                <i class="fa-solid fa-id-card"></i> Trocar Motorista
                            </button>
                            <button class="actions-menu-item" onclick="fecharActionsMenu(); abrirModalTroca(${e.id}, 'ajudante')">
                                <i class="fa-solid fa-user-gear"></i> Trocar Ajudante
                            </button>
                            <button class="actions-menu-item" onclick="fecharActionsMenu(); abrirModalTroca(${e.id}, 'frota')">
                                <i class="fa-solid fa-truck"></i> Trocar Frota
                            </button>
                            <button class="actions-menu-item" onclick="fecharActionsMenu(); abrirModalTroca(${e.id}, 'rota')">
                                <i class="fa-solid fa-route"></i> Trocar Rota
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <tr class="${rowClass}">
                <td><strong>#${e.id}</strong></td>
                <td><strong>${e.motorista}</strong></td>
                <td>${e.ajudante || '<span class="text-muted">Sem ajudante</span>'}</td>
                <td><strong>Frota ${e.numero_frota}</strong> (${e.placa})</td>
                <td>${e.nome_rota}</td>
                <td>${formatarData(e.data_saida)}</td>
                <td>${e.data_chegada ? formatarData(e.data_chegada) : "—"}</td>
                <td>${statusHtml}</td>
                <td>${acoes}</td>
            </tr>
        `;
    }).join("");
}

function mudarSubAbaEscalas(nomeSubAba) {
    document.querySelectorAll("[data-subtab-escala]").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-subtab-escala") === nomeSubAba);
    });
    document.querySelectorAll("#tab-escalas .subtab-content").forEach(c => {
        c.classList.toggle("active", c.id === `subtab-${nomeSubAba}`);
    });
}

// ============================================================
// 3. COLABORADORES & RESERVAS
// ============================================================
function mudarSubAbaColaborador(subtabId) {
    const sec = document.getElementById("tab-colaboradores");
    sec.querySelectorAll(".subtab-content").forEach(el => el.classList.remove("active"));
    sec.querySelectorAll(".sub-nav-btn").forEach(btn => btn.classList.remove("active"));

    document.getElementById("subtab-" + subtabId).classList.add("active");
    const btn = sec.querySelector(`[data-subtab="${subtabId}"]`);
    if (btn) btn.classList.add("active");

    if (subtabId === "colab-reservas") {
        carregarReservas();
    }
}

async function carregarColaboradores() {
    try {
        const colaboradores = await window.api.get("/api/colaboradores");
        const tbody = document.querySelector("#tabela-colaboradores tbody");

        // Atualiza selects de colaboradores
        const selectAfast = document.getElementById("afast-colaborador");
        if (selectAfast) {
            selectAfast.innerHTML = '<option value="">Selecione o colaborador...</option>' +
                colaboradores.filter(c => c.status !== "afastado").map(c => `<option value="${c.id}">${c.nome} (${c.funcao})</option>`).join("");
        }

        const selectHist = document.getElementById("select-historico-colaborador");
        if (selectHist) {
            selectHist.innerHTML = '<option value="">Selecione o colaborador...</option>' +
                colaboradores.map(c => `<option value="${c.id}">${c.nome} (${c.funcao})</option>`).join("");
        }

        if (colaboradores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum colaborador cadastrado.</td></tr>';
            return;
        }

        tbody.innerHTML = colaboradores.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td><strong>${c.nome}</strong></td>
                <td><span class="text-capitalize">${c.funcao}</span></td>
                <td><span class="badge badge-${c.status}">${c.status.replace("_", " ")}</span></td>
                <td>
                    <div class="actions-cell">
                        <button class="btn btn-secondary btn-sm" onclick="verHistoricoColaborador(${c.id})" title="Ficha e Histórico">
                            <i class="fa-solid fa-clock-rotate-left"></i> Histórico
                        </button>
                        ${c.status !== "afastado" ? `
                            <button class="btn btn-warning btn-sm" onclick="abrirModalAfastamentoRapido(${c.id})" title="Afastar">
                                <i class="fa-solid fa-user-slash"></i> Afastar
                            </button>
                        ` : ""}
                    </div>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar colaboradores:", err);
    }
}

async function carregarReservas() {
    try {
        const data = await window.api.get("/api/colaboradores/reserva");
        const tbody = document.querySelector("#tabela-reservas tbody");
        const badge = document.getElementById("total-reservas");
        if (badge) badge.textContent = `${data.length} reserva(s)`;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum colaborador em reserva no momento.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td><strong>${c.nome}</strong></td>
                <td><span class="text-capitalize">${c.funcao}</span></td>
                <td><span class="badge badge-reserva">Reserva</span></td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="removerReserva(${c.id})" title="Liberar para Disponível">
                        <i class="fa-solid fa-user-check"></i> Disponibilizar
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar reservas:", err);
    }
}

async function removerReserva(colaboradorId) {
    if (!confirm("Deseja remover este colaborador da reserva e torná-lo disponível?")) return;
    try {
        await window.api.post(`/api/colaboradores/${colaboradorId}/remover-reserva`);
        mostrarToast("Colaborador liberado com sucesso!", "success");
        carregarReservas();
        carregarColaboradores();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao remover reserva", "error");
    }
}

function verHistoricoColaborador(colaboradorId) {
    mudarSubAbaColaborador("colab-historico");
    const select = document.getElementById("select-historico-colaborador");
    if (select) {
        select.value = colaboradorId;
        carregarHistoricoColaborador(colaboradorId);
    }
}

async function carregarHistoricoColaborador(colaboradorId) {
    const cardPerfil = document.getElementById("card-perfil-colaborador");
    const painelDetalhes = document.getElementById("detalhes-historico-colaborador");

    if (!colaboradorId) {
        if (cardPerfil) cardPerfil.style.display = "none";
        if (painelDetalhes) painelDetalhes.style.display = "none";
        return;
    }

    try {
        const data = await window.api.get(`/api/colaboradores/${colaboradorId}/historico`);

        document.getElementById("perfil-nome-funcao").textContent = `${data.colaborador.nome} (${data.colaborador.funcao})`;
        document.getElementById("perfil-total-viagens").textContent = data.total_viagens || 0;
        document.getElementById("perfil-total-afastamentos").textContent = data.total_afastamentos || 0;
        document.getElementById("perfil-status-atual").innerHTML = `<span class="badge badge-${data.colaborador.status}">${data.colaborador.status.replace("_", " ")}</span>`;

        cardPerfil.style.display = "grid";
        painelDetalhes.style.display = "grid";

        // Tabela de Viagens
        const tbodyEscalas = document.querySelector("#tabela-historico-escalas tbody");
        if (data.escalas && data.escalas.length > 0) {
            tbodyEscalas.innerHTML = data.escalas.map(e => `
                <tr>
                    <td><strong>#${e.id}</strong></td>
                    <td><span class="badge ${e.papel_exercido === 'Motorista' ? 'badge-em_rota' : 'badge-substituido'}">${e.papel_exercido}</span></td>
                    <td>${e.nome_rota}</td>
                    <td>Frota ${e.numero_frota} (${e.placa})</td>
                    <td>${formatarData(e.data_saida)}</td>
                    <td>${e.data_chegada ? formatarData(e.data_chegada) : "—"}</td>
                    <td><span class="badge badge-${e.status}">${e.status === "em_rota" ? "Em Rota" : (e.status === "chegou" ? "Chegou" : "Substituído")}</span></td>
                </tr>
            `).join("");
        } else {
            tbodyEscalas.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma viagem registrada.</td></tr>';
        }

        // Tabela de Afastamentos
        const tbodyAfast = document.querySelector("#tabela-historico-afastamentos tbody");
        if (data.afastamentos && data.afastamentos.length > 0) {
            tbodyAfast.innerHTML = data.afastamentos.map(a => `
                <tr>
                    <td><strong>#${a.id}</strong></td>
                    <td>${a.motivo}</td>
                    <td>${formatarData(a.data_inicio)}</td>
                    <td>${a.data_fim_prevista ? formatarData(a.data_fim_prevista) : "Sem previsão"}</td>
                    <td>${a.data_retorno ? formatarData(a.data_retorno) : '<span class="badge badge-afastado">Ativo</span>'}</td>
                </tr>
            `).join("");
        } else {
            tbodyAfast.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum afastamento registrado.</td></tr>';
        }
    } catch (err) {
        mostrarToast("Erro ao carregar ficha do colaborador", "error");
    }
}

// ============================================================
// 4. FROTA & HISTÓRICO DE FROTA
// ============================================================
function mudarSubAbaFrota(subtabId) {
    const sec = document.getElementById("tab-frota");
    sec.querySelectorAll(".subtab-content").forEach(el => el.classList.remove("active"));
    sec.querySelectorAll(".sub-nav-btn").forEach(btn => btn.classList.remove("active"));

    document.getElementById("subtab-" + subtabId).classList.add("active");
    const btn = sec.querySelector(`[data-subtab-frota="${subtabId}"]`);
    if (btn) btn.classList.add("active");

    if (subtabId === "frota-historico") {
        carregarFrotasParaSelectHistorico();
    }
}

async function carregarFrota() {
    try {
        const frota = await window.api.get("/api/frota");
        const tbody = document.querySelector("#tabela-frota tbody");

        if (frota.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">Nenhum veículo cadastrado.</td></tr>';
            return;
        }

        tbody.innerHTML = frota.map(f => `
            <tr>
                <td><strong>#${f.id}</strong></td>
                <td><strong>Frota ${f.numero_frota}</strong></td>
                <td><code>${f.placa}</code></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar frota:", err);
    }
}

async function carregarFrotasParaSelectHistorico() {
    try {
        const frotas = await window.api.get("/api/frota");
        const select = document.getElementById("select-frota-historico");
        if (!select) return;
        const atual = select.value;
        select.innerHTML = '<option value="">Selecione uma frota...</option>' +
            frotas.map(f => `<option value="${f.id}">Frota ${f.numero_frota} - ${f.placa}</option>`).join("");
        if (atual) select.value = atual;
    } catch (err) {
        console.error("Erro ao carregar lista de frotas:", err);
    }
}

async function buscarHistoricoFrota() {
    const frotaId = document.getElementById("select-frota-historico").value;
    if (!frotaId) {
        mostrarToast("Selecione um veículo da frota", "error");
        return;
    }

    const dataInicio = document.getElementById("frota-hist-data-inicio").value;
    const dataFim = document.getElementById("frota-hist-data-fim").value;

    let url = `/api/frotas/${frotaId}/historico`;
    const params = [];
    if (dataInicio) params.push(`data_inicio=${dataInicio}`);
    if (dataFim) params.push(`data_fim=${dataFim}`);
    if (params.length) url += "?" + params.join("&");

    try {
        const data = await window.api.get(url);
        renderHistoricoFrota(data);
    } catch (err) {
        mostrarToast("Erro ao buscar histórico da frota", "error");
    }
}

function renderHistoricoFrota(data) {
    document.getElementById("frota-historico-resultado").style.display = "block";
    const frota = data.frota;
    const historico = data.historico;

    document.getElementById("frota-hist-info").innerHTML = `
        <div class="kpi-card blue">
            <div class="kpi-icon"><i class="fa-solid fa-truck"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Frota</span>
                <h3>${frota.numero_frota}</h3>
            </div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-icon"><i class="fa-solid fa-id-card"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Placa</span>
                <h3>${frota.placa}</h3>
            </div>
        </div>
        <div class="kpi-card teal">
            <div class="kpi-icon"><i class="fa-solid fa-route"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Registros</span>
                <h3>${historico.length}</h3>
            </div>
        </div>
    `;

    document.getElementById("frota-hist-total").textContent = `${historico.length} registro(s)`;
    const tbody = document.querySelector("#tabela-frota-historico tbody");

    if (historico.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum registro encontrado para esta frota.</td></tr>';
        return;
    }

    tbody.innerHTML = historico.map(h => `
        <tr>
            <td>${formatarData(h.data_saida)}</td>
            <td>${h.data_chegada ? formatarData(h.data_chegada) : "—"}</td>
            <td><strong>${h.motorista_nome}</strong></td>
            <td>${h.ajudante_nome || "—"}</td>
            <td>${h.nome_rota}</td>
            <td><span class="badge badge-${h.status}">${h.status === "em_rota" ? "Em Rota" : (h.status === "chegou" ? "Chegou" : "Substituído")}</span></td>
        </tr>
    `).join("");
}

function limparHistoricoFrota() {
    document.getElementById("select-frota-historico").value = "";
    document.getElementById("frota-hist-data-inicio").value = "";
    document.getElementById("frota-hist-data-fim").value = "";
    document.getElementById("frota-historico-resultado").style.display = "none";
}

// ============================================================
// 5. ROTAS, AFASTAMENTOS & AUDITORIA
// ============================================================
async function carregarRotas() {
    try {
        const rotas = await window.api.get("/api/rotas");
        const tbody = document.querySelector("#tabela-rotas tbody");

        if (rotas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">Nenhuma rota cadastrada.</td></tr>';
            return;
        }

        tbody.innerHTML = rotas.map(r => `
            <tr>
                <td><strong>#${r.id}</strong></td>
                <td><strong>${r.nome_rota}</strong></td>
                <td>${r.duracao_media_dias ? `${r.duracao_media_dias} dia(s)` : "Não estimada"}</td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar rotas:", err);
    }
}

async function carregarAfastamentos() {
    try {
        const afastamentos = await window.api.get("/api/afastamentos");
        const tbody = document.querySelector("#tabela-afastamentos tbody");

        if (afastamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum afastamento ativo.</td></tr>';
            return;
        }

        tbody.innerHTML = afastamentos.map(a => `
            <tr>
                <td><strong>#${a.id}</strong></td>
                <td><strong>${a.nome}</strong></td>
                <td><span class="text-capitalize">${a.funcao}</span></td>
                <td><span class="badge badge-afastado">${a.motivo}</span></td>
                <td>${formatarData(a.data_inicio)}</td>
                <td>${a.data_fim_prevista ? formatarData(a.data_fim_prevista) : "Sem previsão"}</td>
                <td>
                    <button class="btn btn-success btn-sm" onclick="abrirModalRetorno(${a.id}, ${a.colaborador_id})">
                        <i class="fa-solid fa-user-check"></i> Retorno
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar afastamentos:", err);
    }
}

async function carregarHistorico() {
    try {
        const historico = await window.api.get("/api/historico");
        const tbody = document.querySelector("#tabela-historico tbody");

        if (historico.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum registro de auditoria.</td></tr>';
            return;
        }

        tbody.innerHTML = historico.map(h => `
            <tr>
                <td><strong>#${h.id}</strong></td>
                <td><span class="badge badge-substituido">${h.tipo_alteracao}</span></td>
                <td>${h.escala_id ? `#${h.escala_id}` : "—"}</td>
                <td>${h.descricao}</td>
                <td><small>${h.data_alteracao}</small></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
    }
}

// ============================================================
// 6. CADASTROS VIA FORMULÁRIO
// ============================================================
async function salvarColaborador(e) {
    e.preventDefault();
    const nome = document.getElementById("colab-nome").value.trim();
    const funcao = document.getElementById("colab-funcao").value;

    try {
        await window.api.post("/api/colaboradores", { nome, funcao });
        mostrarToast("Colaborador cadastrado com sucesso!", "success");
        document.getElementById("form-colaborador").reset();
        carregarColaboradores();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao salvar colaborador", "error");
    }
}

async function salvarFrota(e) {
    e.preventDefault();
    const numero_frota = document.getElementById("frota-numero").value.trim();
    const placa = document.getElementById("frota-placa").value.trim();

    try {
        await window.api.post("/api/frota", { numero_frota, placa });
        mostrarToast("Veículo adicionado à frota!", "success");
        document.getElementById("form-frota").reset();
        carregarFrota();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao salvar veículo", "error");
    }
}

async function salvarRota(e) {
    e.preventDefault();
    const nome_rota = document.getElementById("rota-nome").value.trim();
    const duracao_media_dias = document.getElementById("rota-duracao").value;

    try {
        await window.api.post("/api/rotas", { nome_rota, duracao_media_dias });
        mostrarToast("Rota cadastrada com sucesso!", "success");
        document.getElementById("form-rota").reset();
        carregarRotas();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao salvar rota", "error");
    }
}

async function salvarAfastamento(e) {
    e.preventDefault();
    const colaborador_id = document.getElementById("afast-colaborador").value;
    const motivo = document.getElementById("afast-motivo").value.trim();
    const data_inicio = document.getElementById("afast-inicio").value;
    const data_fim_prevista = document.getElementById("afast-fim").value;

    try {
        await window.api.post("/api/afastamentos", { colaborador_id, motivo, data_inicio, data_fim_prevista });
        mostrarToast("Afastamento registrado!", "success");
        document.getElementById("form-afastamento").reset();
        carregarAfastamentos();
        carregarColaboradores();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao registrar afastamento", "error");
    }
}

// ============================================================
// 7. MODAIS E OPERAÇÕES DE ESCALAS
// ============================================================
async function abrirModalNovaEscala() {
    try {
        const [motoristas, ajudantes, frotas, rotas] = await Promise.all([
            window.api.get("/api/colaboradores/disponiveis/motorista"),
            window.api.get("/api/colaboradores/disponiveis/ajudante"),
            window.api.get("/api/frota"),
            window.api.get("/api/rotas")
        ]);

        document.getElementById("escala-motorista").innerHTML = '<option value="">Selecione o motorista...</option>' +
            motoristas.map(m => `<option value="${m.id}">${m.nome}</option>`).join("");

        document.getElementById("escala-ajudante").innerHTML = '<option value="">Nenhum ajudante</option>' +
            ajudantes.map(a => `<option value="${a.id}">${a.nome}</option>`).join("");

        document.getElementById("escala-frota").innerHTML = '<option value="">Selecione o veículo...</option>' +
            frotas.map(f => `<option value="${f.id}">Frota ${f.numero_frota} (${f.placa})</option>`).join("");

        document.getElementById("escala-rota").innerHTML = '<option value="">Selecione a rota...</option>' +
            rotas.map(r => `<option value="${r.id}">${r.nome_rota}</option>`).join("");

        document.getElementById("escala-saida").value = obterDataHoje();
        abrirModal("modal-escala");
    } catch (err) {
        mostrarToast("Erro ao carregar dados para nova escala", "error");
    }
}

async function salvarNovaEscala(e) {
    e.preventDefault();
    const motorista_id = document.getElementById("escala-motorista").value;
    const ajudante_id = document.getElementById("escala-ajudante").value || null;
    const frota_id = document.getElementById("escala-frota").value;
    const rota_id = document.getElementById("escala-rota").value;
    const data_saida = document.getElementById("escala-saida").value;

    try {
        await window.api.post("/api/escalas", { motorista_id, ajudante_id, frota_id, rota_id, data_saida });
        mostrarToast("Escala lançada com sucesso!", "success");
        fecharModal("modal-escala");
        carregarEscalas();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao lançar escala", "error");
    }
}

async function abrirModalTroca(escalaId, tipo) {
    document.getElementById("troca-escala-id").value = escalaId;
    document.getElementById("troca-tipo").value = tipo;
    document.getElementById("troca-data").value = obterDataHoje();

    const selectNovo = document.getElementById("troca-novo-id");
    const labelSelect = document.getElementById("label-troca-select");
    const modalTitulo = document.getElementById("modal-troca-titulo");

    try {
        if (tipo === "motorista") {
            modalTitulo.innerHTML = '<i class="fa-solid fa-id-card"></i> Substituir Motorista na Viagem';
            labelSelect.textContent = "Novo Motorista Disponível *";
            const motoristas = await window.api.get("/api/colaboradores/disponiveis/motorista");
            selectNovo.innerHTML = '<option value="">Selecione o motorista...</option>' +
                motoristas.map(m => `<option value="${m.id}">${m.nome}</option>`).join("");
        } else if (tipo === "ajudante") {
            modalTitulo.innerHTML = '<i class="fa-solid fa-user-gear"></i> Substituir Ajudante na Viagem';
            labelSelect.textContent = "Novo Ajudante Disponível";
            const ajudantes = await window.api.get("/api/colaboradores/disponiveis/ajudante");
            selectNovo.innerHTML = '<option value="">Nenhum / Remover Ajudante</option>' +
                ajudantes.map(a => `<option value="${a.id}">${a.nome}</option>`).join("");
        } else if (tipo === "frota") {
            modalTitulo.innerHTML = '<i class="fa-solid fa-truck"></i> Substituir Veículo da Frota';
            labelSelect.textContent = "Novo Veículo *";
            const frotas = await window.api.get("/api/frota");
            selectNovo.innerHTML = '<option value="">Selecione o veículo...</option>' +
                frotas.map(f => `<option value="${f.id}">Frota ${f.numero_frota} (${f.placa})</option>`).join("");
        } else if (tipo === "rota") {
            modalTitulo.innerHTML = '<i class="fa-solid fa-route"></i> Substituir Rota de Destino';
            labelSelect.textContent = "Nova Rota *";
            const rotas = await window.api.get("/api/rotas");
            selectNovo.innerHTML = '<option value="">Selecione a rota...</option>' +
                rotas.map(r => `<option value="${r.id}">${r.nome_rota}</option>`).join("");
        }

        abrirModal("modal-troca");
    } catch (err) {
        mostrarToast("Erro ao abrir substituição", "error");
    }
}

async function confirmarTrocaEscala(e) {
    e.preventDefault();
    const escalaId = document.getElementById("troca-escala-id").value;
    const tipo = document.getElementById("troca-tipo").value;
    const novoId = document.getElementById("troca-novo-id").value;
    const dataTroca = document.getElementById("troca-data").value;

    const endpoint = `/api/escalas/${escalaId}/trocar-${tipo}`;
    const body = { data_troca: dataTroca };

    if (tipo === "motorista") body.novo_motorista_id = novoId;
    if (tipo === "ajudante") body.novo_ajudante_id = novoId || null;
    if (tipo === "frota") body.nova_frota_id = novoId;
    if (tipo === "rota") body.nova_rota_id = novoId;

    try {
        await window.api.post(endpoint, body);
        mostrarToast("Substituição realizada com sucesso!", "success");
        fecharModal("modal-troca");
        carregarEscalas();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro na substituição", "error");
    }
}

function abrirModalChegada(escalaId) {
    document.getElementById("chegada-escala-id").value = escalaId;
    document.getElementById("chegada-data").value = obterDataHoje();
    abrirModal("modal-chegada");
}

async function confirmarChegada(e) {
    e.preventDefault();
    const escalaId = document.getElementById("chegada-escala-id").value;
    const dataChegada = document.getElementById("chegada-data").value;

    try {
        await window.api.post(`/api/escalas/${escalaId}/chegada`, { data_chegada: dataChegada });
        mostrarToast("Viagem concluída e colaboradores liberados!", "success");
        fecharModal("modal-chegada");
        carregarEscalas();
        carregarColaboradores();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao registrar chegada", "error");
    }
}

function abrirModalAfastamentoRapido(colaboradorId) {
    mudarAba("afastamentos");
    const select = document.getElementById("afast-colaborador");
    if (select) select.value = colaboradorId;
}

function abrirModalRetorno(afastamentoId, colaboradorId) {
    document.getElementById("retorno-afastamento-id").value = afastamentoId;
    document.getElementById("retorno-colaborador-id").value = colaboradorId;
    document.getElementById("retorno-data").value = obterDataHoje();
    abrirModal("modal-retorno");
}

async function confirmarRetornoAfastamento(e) {
    e.preventDefault();
    const afastamentoId = document.getElementById("retorno-afastamento-id").value;
    const colaboradorId = document.getElementById("retorno-colaborador-id").value;
    const dataRetorno = document.getElementById("retorno-data").value;

    try {
        await window.api.post(`/api/afastamentos/${afastamentoId}/retorno`, {
            colaborador_id: colaboradorId,
            data_retorno: dataRetorno
        });
        mostrarToast("Retorno confirmado! Colaborador disponível.", "success");
        fecharModal("modal-retorno");
        carregarAfastamentos();
        carregarColaboradores();
        carregarIndicadores();
    } catch (err) {
        mostrarToast(err.message || "Erro ao registrar retorno", "error");
    }
}

// ============================================================
// 8. IMPORTAÇÃO E EXPORTAÇÃO EXCEL / CSV
// ============================================================
function abrirModalImportarExcel() {
    document.getElementById("form-importar-excel").reset();
    document.getElementById("import-resultado").style.display = "none";
    abrirModal("modal-importar-excel");
}

async function confirmarImportacaoExcel(e) {
    e.preventDefault();
    const inputArquivo = document.getElementById("excel-arquivo");
    const motivoAfastamento = document.getElementById("excel-motivo").value.trim();
    const btnSubmit = document.getElementById("btn-importar-submit");
    const panelResultado = document.getElementById("import-resultado");

    if (!inputArquivo.files || inputArquivo.files.length === 0) {
        mostrarToast("Selecione um arquivo de planilha", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", inputArquivo.files[0]);
    formData.append("motivo_afastamento", motivoAfastamento);

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processando...';

    try {
        const data = await window.api.upload("/api/importar-excel", formData);
        mostrarToast("Importação concluída com sucesso!", "success");
        panelResultado.style.display = "block";
        panelResultado.innerHTML = `
            <h4><i class="fa-solid fa-circle-check" style="color: var(--success);"></i> Resultado da Importação:</h4>
            <ul>
                <li><strong>Linhas processadas:</strong> ${data.total_linhas}</li>
                <li><strong>Escalas criadas/atualizadas:</strong> ${data.escalas_criadas}</li>
                <li><strong>Afastamentos gerados:</strong> ${data.afastamentos_gerados}</li>
                ${data.erros > 0 ? `<li style="color: var(--danger);"><strong>Erros:</strong> ${data.erros}</li>` : ""}
            </ul>
        `;
        carregarDadosIniciais();
    } catch (err) {
        mostrarToast(err.message || "Erro ao processar planilha", "error");
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = "Processar Importação";
    }
}

async function confirmarImportacaoExcelPage(e) {
    e.preventDefault();
    const inputArquivo = document.getElementById("excel-arquivo-page");
    const motivoAfastamento = document.getElementById("excel-motivo-page").value;
    const btnSubmit = document.getElementById("btn-importar-page-submit");
    const panelResultado = document.getElementById("import-resultado-page");

    if (!inputArquivo.files || inputArquivo.files.length === 0) {
        mostrarToast("Selecione um arquivo de planilha", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", inputArquivo.files[0]);
    formData.append("motivo_afastamento", motivoAfastamento);

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processando...';

    try {
        const data = await window.api.upload("/api/importar-excel", formData);
        mostrarToast("Alteração em massa concluída!", "success");
        panelResultado.style.display = "block";
        panelResultado.innerHTML = `
            <h4><i class="fa-solid fa-circle-check" style="color: var(--success);"></i> Resultado:</h4>
            <ul>
                <li><strong>Total de linhas lidas:</strong> ${data.total_linhas}</li>
                <li><strong>Escalas geradas:</strong> ${data.escalas_criadas}</li>
                <li><strong>Afastamentos gerados:</strong> ${data.afastamentos_gerados}</li>
                ${data.erros > 0 ? `<li style="color: var(--danger);"><strong>Erros:</strong> ${data.erros}</li>` : ""}
            </ul>
        `;
        carregarDadosIniciais();
    } catch (err) {
        mostrarToast(err.message || "Erro na importação", "error");
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Processar Alteração em Massa';
    }
}

function exportarEscalasExcel() {
    mostrarToast("Gerando planilha Excel...", "success");
    window.api.download("/api/escalas/exportar/excel", "escalas_logiscale.xlsx")
        .catch(err => mostrarToast("Falha ao exportar Excel", "error"));
}

function exportarEscalasCsv() {
    mostrarToast("Gerando arquivo CSV...", "success");
    window.api.download("/api/escalas/exportar/csv", "escalas_logiscale.csv")
        .catch(err => mostrarToast("Falha ao exportar CSV", "error"));
}

// ============================================================
// 9. AUTENTICAÇÃO UI & CONFIGURAÇÕES
// ============================================================
function inicializarAuthUI() {
    window.authService.onAuthStateChanged(user => {
        const spanUser = document.getElementById("user-display-name");
        const spanRole = document.getElementById("user-role-badge");
        if (user) {
            if (spanUser) spanUser.textContent = user.nome || user.email;
            if (spanRole) {
                spanRole.textContent = user.role;
                spanRole.className = `badge ${user.role === 'ADMIN' ? 'badge-admin' : 'badge-operacional'}`;
            }
        }
    });
}

function abrirModalLogin(mensagem = "") {
    const infoEl = document.getElementById("login-aviso");
    if (infoEl) {
        infoEl.textContent = mensagem;
        infoEl.style.display = mensagem ? "block" : "none";
    }
    abrirModal("modal-login");
}

async function executarLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const pass = document.getElementById("login-pass").value;

    const res = await window.authService.login(email, pass);
    if (res.success) {
        mostrarToast(`Bem-vindo, ${window.authService.getUser().nome}!`, "success");
        fecharModal("modal-login");
        carregarDadosIniciais();
    } else {
        mostrarToast(res.error || "Erro ao realizar login", "error");
    }
}

function executarLogout() {
    if (confirm("Deseja encerrar sua sessão?")) {
        window.authService.logout();
        mostrarToast("Sessão encerrada.", "success");
    }
}

function abrirModalConfig() {
    document.getElementById("config-api-url").value = window.APP_CONFIG.API_BASE_URL;
    abrirModal("modal-config");
}

function salvarConfigApi(e) {
    e.preventDefault();
    const url = document.getElementById("config-api-url").value.trim();
    window.APP_CONFIG.setApiUrl(url);
    fecharModal("modal-config");
}

// ============================================================
// 10. UTILITÁRIOS GERAIS
// ============================================================
function abrirModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add("active");
}

function fecharModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove("active");
}

function obterDataHoje() {
    return new Date().toISOString().split("T")[0];
}

function formatarData(dataStr) {
    if (!dataStr) return "—";
    const partes = dataStr.split("T")[0].split("-");
    if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    return dataStr;
}

function filtrarTabela(tabelaId, termo) {
    termo = termo.toLowerCase();
    const rows = document.querySelectorAll(`#${tabelaId} tbody tr`);
    rows.forEach(row => {
        const texto = row.textContent.toLowerCase();
        row.style.display = texto.includes(termo) ? "" : "none";
    });
}

function mostrarToast(mensagem, tipo = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    toast.innerHTML = `
        <i class="fa-solid ${tipo === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
        <span>${mensagem}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function toggleActionsMenu(btn, event) {
    event.stopPropagation();
    document.querySelectorAll(".actions-menu.open").forEach(m => {
        if (m !== btn.nextElementSibling) m.classList.remove("open");
    });
    const menu = btn.nextElementSibling;
    if (menu) menu.classList.toggle("open");
}

function fecharActionsMenu() {
    document.querySelectorAll(".actions-menu.open").forEach(m => m.classList.remove("open"));
}

document.addEventListener("click", (e) => {
    if (!e.target.closest(".actions-dropdown")) {
        fecharActionsMenu();
    }
});
