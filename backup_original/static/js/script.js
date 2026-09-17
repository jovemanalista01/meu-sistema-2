/* ==========================================================================
   GESTAO OPERACIONAL DE FROTA - LÓGICA JAVASCRIPT FRONTEND
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    inicializarNavegacao();
    carregarDadosIniciais();
});

// --- STATE DA APLICAÇÃO ---
let abaAtual = 'dashboard';

// --- INITIALIZERS ---

function inicializarNavegacao() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            mudarAba(targetTab);
        });
    });
}

function mudarAba(nomeAba) {
    abaAtual = nomeAba;

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === nomeAba);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${nomeAba}`);
    });

    const titulos = {
        'dashboard': { title: 'Painel & Indicadores', subtitle: 'Visão geral em tempo real da operação de frota e escalas' },
        'escalas': { title: 'Escalas de Viagem', subtitle: 'Acompanhamento de rotas em andamento, concluídas e trocas' },
        'colaboradores': { title: 'Gestão de Colaboradores', subtitle: 'Cadastro e controle de motoristas e ajudantes' },
        'frota': { title: 'Frota Pesada', subtitle: 'Cadastro de veículos e placas da frota' },
        'rotas': { title: 'Rotas Operacionais', subtitle: 'Destinos e tempo médio estimado de viagem' },
        'afastamentos': { title: 'Afastamentos e Licenças', subtitle: 'Controle de saídas por férias ou atestado médico' },
        'historico': { title: 'Histórico & Auditoria', subtitle: 'Trilha completa de alterações e substituições' }
    };

    if (titulos[nomeAba]) {
        document.getElementById('page-title').textContent = titulos[nomeAba].title;
        document.getElementById('page-subtitle').textContent = titulos[nomeAba].subtitle;
    }

    recarregarDadosAba(nomeAba);
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

function recarregarDadosAtuais() {
    recarregarDadosAba(abaAtual);
    carregarIndicadores();
    mostrarToast('Dados atualizados com sucesso!', 'success');
}

function recarregarDadosAba(nomeAba) {
    switch (nomeAba) {
        case 'dashboard': carregarIndicadores(); break;
        case 'escalas': carregarEscalas(); break;
        case 'colaboradores': carregarColaboradores(); break;
        case 'frota': carregarFrota(); break;
        case 'rotas': carregarRotas(); break;
        case 'afastamentos': carregarAfastamentos(); break;
        case 'historico': carregarHistorico(); break;
    }
}


// --- 1. CARREGAMENTO DE DADOS (FETCH APIS) ---

async function carregarIndicadores() {
    try {
        const res = await fetch('/api/indicadores');
        const data = await res.json();

        // KPIs existentes
        document.getElementById('kpi-escalas-em-rota').textContent = data.escalas_em_rota || 0;
        document.getElementById('kpi-motoristas-disponiveis').textContent = data.motoristas_disponiveis || 0;
        document.getElementById('kpi-ajudantes-disponiveis').textContent = data.ajudantes_disponiveis || 0;
        document.getElementById('kpi-colaboradores-afastados').textContent = data.colaboradores_afastados || 0;
        document.getElementById('kpi-pontualidade').textContent = `${data.taxa_pontualidade}%`;

        // NOVOS KPIs
        atualizarNovosKPIs(data);
        carregarFrotasDisponiveis();

        // Renderiza Top Motoristas
        const topMotList = document.getElementById('list-top-motoristas');
        if (data.top_motoristas && data.top_motoristas.length > 0) {
            topMotList.innerHTML = data.top_motoristas.map((m, idx) => `
                <li class="rank-item">
                    <div class="rank-info">
                        <span class="rank-num">#${idx + 1}</span>
                        <strong>${m.nome}</strong>
                    </div>
                    <span class="rank-badge">${m.total_viagens} viagem(ns)</span>
                </li>
            `).join('');
        } else {
            topMotList.innerHTML = '<li class="rank-item">Nenhum dado registrado</li>';
        }

        // Renderiza Top Rotas
        const topRotasList = document.getElementById('list-top-rotas');
        if (data.top_rotas && data.top_rotas.length > 0) {
            topRotasList.innerHTML = data.top_rotas.map((r, idx) => `
                <li class="rank-item">
                    <div class="rank-info">
                        <span class="rank-num">#${idx + 1}</span>
                        <strong>${r.nome_rota}</strong>
                    </div>
                    <span class="rank-badge">${r.total_escalas} escala(s)</span>
                </li>
            `).join('');
        } else {
            topRotasList.innerHTML = '<li class="rank-item">Nenhuma rota registrada</li>';
        }
    } catch (err) {
        console.error('Erro ao carregar indicadores:', err);
    }
}

function atualizarNovosKPIs(indicadores) {
    const elFrotas = document.getElementById('kpi-frotas-disponiveis');
    const elReservas = document.getElementById('kpi-reservas');
    const elTransbordos = document.getElementById('kpi-transbordos');

    if (elFrotas) elFrotas.textContent = indicadores.frotas_disponiveis || 0;
    if (elReservas) elReservas.textContent = indicadores.total_reservas || 0;
    if (elTransbordos) elTransbordos.textContent = indicadores.total_transbordos || 0;
}

function carregarFrotasDisponiveis() {
    fetch('/api/frotas/disponiveis')
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('list-frotas-disponiveis');
            if (!list) return;

            if (data.length === 0) {
                list.innerHTML = '<li class="rank-item"><span class="rank-info">Nenhuma frota disponível</span></li>';
                return;
            }

            list.innerHTML = data.map((f, i) => `
                <li class="rank-item">
                    <div class="rank-info">
                        <span class="rank-num">${i + 1}</span>
                        <div>
                            <strong>${f.numero_frota}</strong>
                            <span style="color: var(--text-muted); font-size: 0.8rem;"> — ${f.placa}</span>
                        </div>
                    </div>
                    <span class="badge badge-livre">Livre</span>
                </li>
            `).join('');
        })
        .catch(err => console.error('Erro ao carregar frotas disponíveis:', err));
}

// ============================================================
// STATE DAS ESCALAS
// ============================================================
let escalasData = [];
let filtroEscalas = 'ativas';

function setFiltroEscalas(filtro) {
    filtroEscalas = filtro;
    document.querySelectorAll('#filtro-escalas-tabs .filter-tab').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-filtro') === filtro);
    });
    renderizarEscalas();
}

async function carregarEscalas() {
    try {
        const res = await fetch('/api/escalas');
        escalasData = await res.json();
        console.log(`Escalas carregadas: ${escalasData.length} total`);
        renderizarEscalas();
    } catch (err) {
        console.error('Erro ao carregar escalas:', err);
    }
}

function renderizarEscalas() {
    const tbody = document.querySelector('#tabela-escalas tbody');

    // Aplica filtro de status
    let filtradas = escalasData;
    if (filtroEscalas === 'ativas') {
        filtradas = escalasData.filter(e => e.status === 'em_rota');
    } else if (filtroEscalas === 'concluidas') {
        filtradas = escalasData.filter(e => e.status === 'chegou');
    }
    // 'todas' mostra tudo

    if (filtradas.length === 0) {
        const msg = filtroEscalas === 'ativas' ? 'Nenhuma escala ativa no momento.' :
                    filtroEscalas === 'concluidas' ? 'Nenhuma escala concluída.' :
                    'Nenhuma escala registrada.';
        tbody.innerHTML = `<tr><td colspan="9" class="text-center">${msg}</td></tr>`;
        return;
    }

    tbody.innerHTML = filtradas.map(e => {
        const isSubstituido = e.status === 'substituido';
        const rowClass = isSubstituido ? 'row-substituido' : '';

        // Status: substituido vira indicador sutil
        let statusHtml;
        if (isSubstituido) {
            statusHtml = '<span class="badge-subst" title="Escala substituída">Subst.</span>';
        } else {
            const badgeClass = `badge badge-${e.status}`;
            const texto = e.status === 'em_rota' ? 'Em Rota' : 'Chegou';
            statusHtml = `<span class="${badgeClass}">${texto}</span>`;
        }

        // Ações: só para escalas ativas
        let acoes = '-';
        if (e.status === 'em_rota') {
            acoes = `
                <div class="actions-cell">
                    <button class="btn btn-success btn-sm" onclick="abrirModalChegada(${e.id})" title="Registrar Chegada">
                        <i class="fa-solid fa-flag-checkered"></i> Chegada
                    </button>
                    <div class="actions-dropdown">
                        <button class="actions-toggle" onclick="toggleActionsMenu(this, event)" title="Mais ações">
                            <i class="fa-solid fa-gear"></i>
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
                <td>${e.motorista}</td>
                <td>${e.ajudante || '<span class="text-muted">Sem ajudante</span>'}</td>
                <td><strong>Frota ${e.numero_frota}</strong> (${e.placa})</td>
                <td>${e.nome_rota}</td>
                <td>${formatarData(e.data_saida)}</td>
                <td>${e.data_chegada ? formatarData(e.data_chegada) : '-'}</td>
                <td>${statusHtml}</td>
                <td>${acoes}</td>
            </tr>
        `;
    }).join('');
}

async function carregarColaboradores() {
    try {
        const res = await fetch('/api/colaboradores');
        const colaboradores = await res.json();
        const tbody = document.querySelector('#tabela-colaboradores tbody');
        const selectAfast = document.getElementById('afast-colaborador');

        // Preenche select do formulário de afastamento
        if (selectAfast) {
            selectAfast.innerHTML = '<option value="">Selecione o colaborador...</option>' +
                colaboradores.filter(c => c.status !== 'afastado').map(c => `<option value="${c.id}">${c.nome} (${c.funcao})</option>`).join('');
        }

        // Preenche select do Histórico Individual
        const selectHist = document.getElementById('select-historico-colaborador');
        if (selectHist) {
            selectHist.innerHTML = '<option value="">Selecione o colaborador...</option>' +
                colaboradores.map(c => `<option value="${c.id}">${c.nome} (${c.funcao})</option>`).join('');
        }

        if (colaboradores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum colaborador cadastrado.</td></tr>';
            return;
        }

        tbody.innerHTML = colaboradores.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td>${c.nome}</td>
                <td><span class="text-capitalize">${c.funcao}</span></td>
                <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ')}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="verHistoricoColaborador(${c.id})" title="Ver Histórico Completo">
                            <i class="fa-solid fa-clock-rotate-left"></i> Histórico
                        </button>
                        ${c.status !== 'afastado' ? `
                            <button class="btn btn-warning btn-sm" onclick="abrirModalAfastamentoRapido(${c.id})" title="Registrar Afastamento">
                                <i class="fa-solid fa-user-slash"></i> Afastar
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar colaboradores:', err);
    }
}


// ============================================================
// SUB-ABA ESCALAS
// ============================================================
function mudarSubAbaEscalas(nomeSubAba) {
    document.querySelectorAll('[data-subtab-escala]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-subtab-escala') === nomeSubAba);
    });

    document.querySelectorAll('#tab-escalas .subtab-content').forEach(content => {
        content.classList.toggle('active', content.id === `subtab-${nomeSubAba}`);
    });
}


// ============================================================
// SUB-ABA COLABORADORES (com Reservas)
// ============================================================
function mudarSubAbaColaborador(subtabId) {
    const section = document.getElementById('tab-colaboradores');
    section.querySelectorAll('.subtab-content').forEach(el => el.classList.remove('active'));
    section.querySelectorAll('.sub-nav-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById('subtab-' + subtabId).classList.add('active');
    const btn = section.querySelector(`[data-subtab="${subtabId}"]`);
    if (btn) btn.classList.add('active');

    if (subtabId === 'colab-reservas') {
        carregarReservas();
    }
}


// ============================================================
// SUB-ABA FROTA (Cadastro / Histórico)
// ============================================================
function mudarSubAbaFrota(subtabId) {
    const section = document.getElementById('tab-frota');
    section.querySelectorAll('.subtab-content').forEach(el => el.classList.remove('active'));
    section.querySelectorAll('.sub-nav-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById('subtab-' + subtabId).classList.add('active');
    const btn = section.querySelector(`[data-subtab-frota="${subtabId}"]`);
    if (btn) btn.classList.add('active');

    if (subtabId === 'frota-historico') {
        carregarFrotasParaHistorico();
    }
}


// ============================================================
// RESERVAS
// ============================================================
function carregarReservas() {
    fetch('/api/colaboradores/reserva')
        .then(r => r.json())
        .then(data => {
            const tbody = document.querySelector('#tabela-reservas tbody');
            const badge = document.getElementById('total-reservas');
            badge.textContent = data.length + ' reserva(s)';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum colaborador em reserva</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(c => {
                const funcaoBadge = c.funcao === 'motorista' ? 'badge-motorista' : 'badge-ajudante';
                return `
                    <tr>
                        <td>${c.id}</td>
                        <td><strong>${c.nome}</strong></td>
                        <td><span class="badge ${funcaoBadge}">${c.funcao}</span></td>
                        <td><span class="badge badge-reserva">Reserva</span></td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-success" onclick="removerReserva(${c.id})" title="Disponibilizar">
                                    <i class="fa-solid fa-user-check"></i> Disponibilizar
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        })
        .catch(err => {
            console.error('Erro ao carregar reservas:', err);
        });
}

function removerReserva(colaboradorId) {
    if (!confirm('Remover este colaborador da reserva e deixá-lo disponível?')) return;

    fetch(`/api/colaboradores/${colaboradorId}/remover-reserva`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                mostrarToast(data.error, 'error');
                return;
            }
            mostrarToast('Colaborador disponibilizado com sucesso', 'success');
            carregarReservas();
            carregarColaboradores();
        })
        .catch(err => {
            mostrarToast('Erro ao remover reserva', 'error');
            console.error(err);
        });
}


// ============================================================
// HISTÓRICO DE FROTA
// ============================================================
function carregarFrotasParaHistorico() {
    fetch('/api/frota')
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById('select-frota-historico');
            const atual = select.value;
            select.innerHTML = '<option value="">Selecione uma frota...</option>';
            data.forEach(f => {
                select.innerHTML += `<option value="${f.id}">${f.numero_frota} - ${f.placa}</option>`;
            });
            if (atual) select.value = atual;
        })
        .catch(err => console.error('Erro ao carregar frotas:', err));
}

function buscarHistoricoFrota() {
    const frotaId = document.getElementById('select-frota-historico').value;
    if (!frotaId) {
        mostrarToast('Selecione uma frota', 'error');
        return;
    }

    const dataInicio = document.getElementById('frota-hist-data-inicio').value;
    const dataFim = document.getElementById('frota-hist-data-fim').value;

    let url = `/api/frotas/${frotaId}/historico`;
    const params = [];
    if (dataInicio) params.push(`data_inicio=${dataInicio}`);
    if (dataFim) params.push(`data_fim=${dataFim}`);
    if (params.length) url += '?' + params.join('&');

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (data.erro) {
                mostrarToast(data.erro, 'error');
                return;
            }
            renderHistoricoFrota(data);
        })
        .catch(err => {
            console.error(err);
            mostrarToast('Erro ao buscar histórico', 'error');
        });
}

function renderHistoricoFrota(data) {
    document.getElementById('frota-historico-resultado').style.display = 'block';

    const frota = data.frota;
    const historico = data.historico;
    const temFiltro = document.getElementById('frota-hist-data-inicio').value ||
                      document.getElementById('frota-hist-data-fim').value;

    // Info da frota
    document.getElementById('frota-hist-info').innerHTML = `
        <div class="kpi-card blue">
            <div class="kpi-icon"><i class="fa-solid fa-truck"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Frota</span>
                <h3 style="font-size:1.1rem;">${frota.numero_frota}</h3>
            </div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-icon"><i class="fa-solid fa-id-card"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Placa</span>
                <h3 style="font-size:1.1rem;">${frota.placa}</h3>
            </div>
        </div>
        <div class="kpi-card teal">
            <div class="kpi-icon"><i class="fa-solid fa-list-ol"></i></div>
            <div class="kpi-data">
                <span class="kpi-label">Registros</span>
                <h3 style="font-size:1.1rem;">${historico.length}</h3>
            </div>
        </div>
    `;

    // Título
    document.getElementById('frota-hist-titulo').textContent = temFiltro
        ? 'Resultado filtrado'
        : 'Últimos 3 registros';

    document.getElementById('frota-hist-total').textContent = `${historico.length} registro(s)`;

    // Tabela
    const tbody = document.querySelector('#tabela-frota-historico tbody');

    if (historico.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum registro encontrado</td></tr>';
        return;
    }

    tbody.innerHTML = historico.map(h => {
        const statusClass = h.status === 'em_rota' ? 'badge-em_rota'
            : h.status === 'chegou' ? 'badge-chegou'
            : 'badge-substituido';

        const statusLabel = h.status === 'em_rota' ? 'Em Rota'
            : h.status === 'chegou' ? 'Chegou'
            : 'Substituído';

        return `
            <tr>
                <td>${formatarData(h.data_saida)}</td>
                <td>${h.data_chegada ? formatarData(h.data_chegada) : '—'}</td>
                <td><strong>${h.motorista_nome}</strong></td>
                <td>${h.ajudante_nome || '—'}</td>
                <td>${h.nome_rota}</td>
                <td><span class="badge ${statusClass}">${statusLabel}</span></td>
            </tr>
        `;
    }).join('');
}

function limparHistoricoFrota() {
    document.getElementById('select-frota-historico').value = '';
    document.getElementById('frota-hist-data-inicio').value = '';
    document.getElementById('frota-hist-data-fim').value = '';
    document.getElementById('frota-historico-resultado').style.display = 'none';
}


// ============================================================
// IMPORTAÇÃO EXCEL (sub-aba dentro de Escalas)
// ============================================================
async function confirmarImportacaoExcelPage(e) {
    e.preventDefault();
    const inputArquivo = document.getElementById('excel-arquivo-page');
    const motivoAfastamento = document.getElementById('excel-motivo-page').value;
    const btnSubmit = document.getElementById('btn-importar-page-submit');
    const panelResultado = document.getElementById('import-resultado-page');

    if (!inputArquivo.files || inputArquivo.files.length === 0) {
        mostrarToast('Selecione um arquivo de planilha', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', inputArquivo.files[0]);
    formData.append('motivo_afastamento', motivoAfastamento);

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processando...';

    try {
        const res = await fetch('/api/importar-excel', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            mostrarToast('Alteração em massa concluída com sucesso!', 'success');
            panelResultado.style.display = 'block';
            panelResultado.innerHTML = `
                <h4><i class="fa-solid fa-square-check" style="color: var(--accent-green);"></i> Resultado da Importação:</h4>
                <ul>
                    <li><strong>Total de linhas processadas:</strong> ${data.total_linhas}</li>
                    <li><strong>Escalas geradas/atualizadas:</strong> ${data.escalas_criadas}</li>
                    <li><strong>Afastamentos por remoção de ajudante:</strong> ${data.afastamentos_gerados}</li>
                    ${data.erros > 0 ? `<li style="color: var(--accent-red);"><strong>Erros encontrados:</strong> ${data.erros}</li>` : ''}
                </ul>
            `;

            carregarEscalas();
            carregarColaboradores();
            carregarFrota();
            carregarRotas();
            carregarAfastamentos();
            carregarIndicadores();
            carregarHistorico();
        } else {
            mostrarToast(data.error || 'Erro na alteração em massa', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de comunicação com o servidor', 'error');
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Processar Alteração em Massa';
    }
}


// ============================================================
// HISTÓRICO INDIVIDUAL DO COLABORADOR
// ============================================================
function verHistoricoColaborador(colaboradorId) {
    mudarSubAbaColaborador('colab-historico');
    const select = document.getElementById('select-historico-colaborador');
    if (select) {
        select.value = colaboradorId;
        carregarHistoricoColaborador(colaboradorId);
    }
}

async function carregarHistoricoColaborador(colaboradorId) {
    const cardPerfil = document.getElementById('card-perfil-colaborador');
    const painelDetalhes = document.getElementById('detalhes-historico-colaborador');

    if (!colaboradorId) {
        if (cardPerfil) cardPerfil.style.display = 'none';
        if (painelDetalhes) painelDetalhes.style.display = 'none';
        return;
    }

    try {
        const res = await fetch(`/api/colaboradores/${colaboradorId}/historico`);
        if (!res.ok) {
            mostrarToast('Erro ao carregar histórico do colaborador', 'error');
            return;
        }

        const data = await res.json();

        // 1. Preenche Perfil e KPIs
        document.getElementById('perfil-nome-funcao').textContent = `${data.colaborador.nome} (${data.colaborador.funcao})`;
        document.getElementById('perfil-total-viagens').textContent = data.total_viagens || 0;
        document.getElementById('perfil-total-afastamentos').textContent = data.total_afastamentos || 0;

        const badgeStatus = `<span class="badge badge-${data.colaborador.status}">${data.colaborador.status.replace('_', ' ')}</span>`;
        document.getElementById('perfil-status-atual').innerHTML = badgeStatus;

        cardPerfil.style.display = 'grid';
        painelDetalhes.style.display = 'grid';

        // 2. Preenche Tabela de Escalas / Rotas
        const tbodyEscalas = document.querySelector('#tabela-historico-escalas tbody');
        if (data.escalas && data.escalas.length > 0) {
            tbodyEscalas.innerHTML = data.escalas.map(e => `
                <tr>
                    <td><strong>#${e.id}</strong></td>
                    <td><span class="badge ${e.papel_exercido === 'Motorista' ? 'badge-em_rota' : 'badge-substituido'}">${e.papel_exercido}</span></td>
                    <td>${e.nome_rota}</td>
                    <td>Frota ${e.numero_frota} (${e.placa})</td>
                    <td>${formatarData(e.data_saida)}</td>
                    <td>${e.data_chegada ? formatarData(e.data_chegada) : '-'}</td>
                    <td><span class="badge badge-${e.status}">${e.status === 'em_rota' ? 'Em Rota' : (e.status === 'chegou' ? 'Chegou' : 'Substituído')}</span></td>
                </tr>
            `).join('');
        } else {
            tbodyEscalas.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma viagem registrada para este colaborador.</td></tr>';
        }

        // 3. Preenche Tabela de Afastamentos
        const tbodyAfast = document.querySelector('#tabela-historico-afastamentos tbody');
        if (data.afastamentos && data.afastamentos.length > 0) {
            tbodyAfast.innerHTML = data.afastamentos.map(a => `
                <tr>
                    <td><strong>#${a.id}</strong></td>
                    <td>${a.motivo}</td>
                    <td>${formatarData(a.data_inicio)}</td>
                    <td>${a.data_fim_prevista ? formatarData(a.data_fim_prevista) : 'Sem previsão'}</td>
                    <td>${a.data_retorno ? formatarData(a.data_retorno) : '<span class="badge badge-afastado">Ativo</span>'}</td>
                </tr>
            `).join('');
        } else {
            tbodyAfast.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum afastamento registrado.</td></tr>';
        }

    } catch (err) {
        console.error('Erro ao carregar histórico do colaborador:', err);
        mostrarToast('Erro ao carregar histórico', 'error');
    }
}


// ============================================================
// CARREGAMENTO DE TABELAS SIMPLES
// ============================================================
async function carregarFrota() {
    try {
        const res = await fetch('/api/frota');
        const frota = await res.json();
        const tbody = document.querySelector('#tabela-frota tbody');

        if (frota.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">Nenhum veículo na frota.</td></tr>';
            return;
        }

        tbody.innerHTML = frota.map(f => `
            <tr>
                <td><strong>#${f.id}</strong></td>
                <td><strong>Frota ${f.numero_frota}</strong></td>
                <td><code>${f.placa}</code></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar frota:', err);
    }
}

async function carregarRotas() {
    try {
        const res = await fetch('/api/rotas');
        const rotas = await res.json();
        const tbody = document.querySelector('#tabela-rotas tbody');

        if (rotas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">Nenhuma rota cadastrada.</td></tr>';
            return;
        }

        tbody.innerHTML = rotas.map(r => `
            <tr>
                <td><strong>#${r.id}</strong></td>
                <td>${r.nome_rota}</td>
                <td>${r.duracao_media_dias ? `${r.duracao_media_dias} dia(s)` : 'Não informada'}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar rotas:', err);
    }
}

async function carregarAfastamentos() {
    try {
        const res = await fetch('/api/afastamentos');
        const afastamentos = await res.json();
        const tbody = document.querySelector('#tabela-afastamentos tbody');

        if (afastamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum afastamento ativo no momento.</td></tr>';
            return;
        }

        tbody.innerHTML = afastamentos.map(a => `
            <tr>
                <td><strong>#${a.id}</strong></td>
                <td>${a.nome}</td>
                <td><span class="text-capitalize">${a.funcao}</span></td>
                <td>${a.motivo}</td>
                <td>${formatarData(a.data_inicio)}</td>
                <td>${a.data_fim_prevista ? formatarData(a.data_fim_prevista) : 'Sem previsão'}</td>
                <td>
                    <button class="btn btn-success btn-sm" onclick="abrirModalRetorno(${a.id}, ${a.colaborador_id})">
                        <i class="fa-solid fa-user-check"></i> Registrar Retorno
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar afastamentos:', err);
    }
}

async function carregarHistorico() {
    try {
        const res = await fetch('/api/historico');
        const historico = await res.json();
        const tbody = document.querySelector('#tabela-historico tbody');

        if (historico.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum registro de auditoria.</td></tr>';
            return;
        }

        tbody.innerHTML = historico.map(h => `
            <tr>
                <td><strong>#${h.id}</strong></td>
                <td><span class="badge badge-substituido">${h.tipo_alteracao}</span></td>
                <td>${h.escala_id ? `#${h.escala_id}` : '-'}</td>
                <td>${h.descricao}</td>
                <td><small>${h.data_alteracao}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Erro ao carregar histórico:', err);
    }
}


// --- 2. SUBMISSÃO DE FORMULÁRIOS ---

async function salvarColaborador(e) {
    e.preventDefault();
    const nome = document.getElementById('colab-nome').value.trim();
    const funcao = document.getElementById('colab-funcao').value;

    try {
        const res = await fetch('/api/colaboradores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, funcao })
        });
        if (res.ok) {
            mostrarToast('Colaborador cadastrado!', 'success');
            document.getElementById('form-colaborador').reset();
            carregarColaboradores();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao cadastrar', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao salvar', 'error');
    }
}

async function salvarFrota(e) {
    e.preventDefault();
    const numero_frota = document.getElementById('frota-numero').value.trim();
    const placa = document.getElementById('frota-placa').value.trim();

    try {
        const res = await fetch('/api/frota', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_frota, placa })
        });
        if (res.ok) {
            mostrarToast('Veículo cadastrado!', 'success');
            document.getElementById('form-frota').reset();
            carregarFrota();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao salvar veículo', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao salvar', 'error');
    }
}

async function salvarRota(e) {
    e.preventDefault();
    const nome_rota = document.getElementById('rota-nome').value.trim();
    const duracao_media_dias = document.getElementById('rota-duracao').value;

    try {
        const res = await fetch('/api/rotas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_rota, duracao_media_dias })
        });
        if (res.ok) {
            mostrarToast('Rota cadastrada!', 'success');
            document.getElementById('form-rota').reset();
            carregarRotas();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao salvar rota', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao salvar', 'error');
    }
}

async function salvarAfastamento(e) {
    e.preventDefault();
    const colaborador_id = document.getElementById('afast-colaborador').value;
    const motivo = document.getElementById('afast-motivo').value.trim();
    const data_inicio = document.getElementById('afast-inicio').value;
    const data_fim_prevista = document.getElementById('afast-fim').value;

    try {
        const res = await fetch('/api/afastamentos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ colaborador_id, motivo, data_inicio, data_fim_prevista })
        });
        if (res.ok) {
            mostrarToast('Afastamento registrado!', 'success');
            document.getElementById('form-afastamento').reset();
            carregarAfastamentos();
            carregarColaboradores();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao afastar', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao afastar', 'error');
    }
}

async function salvarNovaEscala(e) {
    e.preventDefault();
    const motorista_id = document.getElementById('escala-motorista').value;
    const ajudante_id = document.getElementById('escala-ajudante').value || null;
    const frota_id = document.getElementById('escala-frota').value;
    const rota_id = document.getElementById('escala-rota').value;
    const data_saida = document.getElementById('escala-saida').value;

    try {
        const res = await fetch('/api/escalas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ motorista_id, ajudante_id, frota_id, rota_id, data_saida })
        });

        if (res.ok) {
            mostrarToast('Escala criada com sucesso!', 'success');
            fecharModal('modal-escala');
            carregarEscalas();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao lançar escala', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao lançar escala', 'error');
    }
}


// --- 3. MODAIS E OPERAÇÕES DE ESCALA ---

async function abrirModalNovaEscala() {
    const resMot = await fetch('/api/colaboradores/disponiveis/motorista');
    const motoristas = await resMot.json();

    const resAjud = await fetch('/api/colaboradores/disponiveis/ajudante');
    const ajudantes = await resAjud.json();

    const resFrota = await fetch('/api/frota');
    const frota = await resFrota.json();

    const resRotas = await fetch('/api/rotas');
    const rotas = await resRotas.json();

    const selMot = document.getElementById('escala-motorista');
    selMot.innerHTML = '<option value="">Selecione o motorista...</option>' +
        motoristas.map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

    const selAjud = document.getElementById('escala-ajudante');
    selAjud.innerHTML = '<option value="">Nenhum ajudante</option>' +
        ajudantes.map(a => `<option value="${a.id}">${a.nome}</option>`).join('');

    const selFrota = document.getElementById('escala-frota');
    selFrota.innerHTML = '<option value="">Selecione o veículo...</option>' +
        frota.map(f => `<option value="${f.id}">Frota ${f.numero_frota} (${f.placa})</option>`).join('');

    const selRotas = document.getElementById('escala-rota');
    selRotas.innerHTML = '<option value="">Selecione a rota...</option>' +
        rotas.map(r => `<option value="${r.id}">${r.nome_rota}</option>`).join('');

    document.getElementById('escala-saida').value = obterDataHoje();

    abrirModal('modal-escala');
}

async function abrirModalTroca(escalaId, tipo) {
    document.getElementById('troca-escala-id').value = escalaId;
    document.getElementById('troca-tipo').value = tipo;
    document.getElementById('troca-data').value = obterDataHoje();

    const selectNovo = document.getElementById('troca-novo-id');
    const labelSelect = document.getElementById('label-troca-select');
    const modalTitulo = document.getElementById('modal-troca-titulo');

    if (tipo === 'motorista') {
        modalTitulo.innerHTML = '<i class="fa-solid fa-id-card"></i> Substituir Motorista na Escala';
        labelSelect.textContent = 'Novo Motorista (Disponível) *';
        const res = await fetch('/api/colaboradores/disponiveis/motorista');
        const disponiveis = await res.json();
        selectNovo.innerHTML = '<option value="">Selecione o novo motorista...</option>' +
            disponiveis.map(d => `<option value="${d.id}">${d.nome}</option>`).join('');
    }
    else if (tipo === 'ajudante') {
        modalTitulo.innerHTML = '<i class="fa-solid fa-user-gear"></i> Substituir Ajudante na Escala';
        labelSelect.textContent = 'Novo Ajudante (Disponível) *';
        const res = await fetch('/api/colaboradores/disponiveis/ajudante');
        const disponiveis = await res.json();
        selectNovo.innerHTML = '<option value="">Nenhum / Remover Ajudante</option>' +
            disponiveis.map(d => `<option value="${d.id}">${d.nome}</option>`).join('');
    }
    else if (tipo === 'frota') {
        modalTitulo.innerHTML = '<i class="fa-solid fa-truck"></i> Substituir Veículo da Frota';
        labelSelect.textContent = 'Novo Veículo *';
        const res = await fetch('/api/frota');
        const frotas = await res.json();
        selectNovo.innerHTML = '<option value="">Selecione o veículo...</option>' +
            frotas.map(f => `<option value="${f.id}">Frota ${f.numero_frota} (${f.placa})</option>`).join('');
    }
    else if (tipo === 'rota') {
        modalTitulo.innerHTML = '<i class="fa-solid fa-route"></i> Substituir Rota de Destino';
        labelSelect.textContent = 'Nova Rota *';
        const res = await fetch('/api/rotas');
        const rotas = await res.json();
        selectNovo.innerHTML = '<option value="">Selecione a rota...</option>' +
            rotas.map(r => `<option value="${r.id}">${r.nome_rota}</option>`).join('');
    }

    abrirModal('modal-troca');
}

async function confirmarTrocaEscala(e) {
    e.preventDefault();
    const escalaId = document.getElementById('troca-escala-id').value;
    const tipo = document.getElementById('troca-tipo').value;
    const novoId = document.getElementById('troca-novo-id').value;
    const dataTroca = document.getElementById('troca-data').value;

    let url = `/api/escalas/${escalaId}/trocar-${tipo}`;
    let body = { data_troca: dataTroca };

    if (tipo === 'motorista') body.novo_motorista_id = novoId;
    if (tipo === 'ajudante') body.novo_ajudante_id = novoId || null;
    if (tipo === 'frota') body.nova_frota_id = novoId;
    if (tipo === 'rota') body.nova_rota_id = novoId;

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (res.ok) {
            mostrarToast('Substituição realizada com sucesso!', 'success');
            fecharModal('modal-troca');
            carregarEscalas();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao realizar troca', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede na substituição', 'error');
    }
}

function abrirModalChegada(escalaId) {
    document.getElementById('chegada-escala-id').value = escalaId;
    document.getElementById('chegada-data').value = obterDataHoje();
    abrirModal('modal-chegada');
}

async function confirmarChegada(e) {
    e.preventDefault();
    const escalaId = document.getElementById('chegada-escala-id').value;
    const dataChegada = document.getElementById('chegada-data').value;

    try {
        const res = await fetch(`/api/escalas/${escalaId}/chegada`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_chegada: dataChegada })
        });

        if (res.ok) {
            mostrarToast('Chegada registrada e colaboradores liberados!', 'success');
            fecharModal('modal-chegada');
            carregarEscalas();
            carregarColaboradores();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao registrar chegada', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao registrar chegada', 'error');
    }
}

function abrirModalAfastamentoRapido(colaboradorId) {
    mudarAba('afastamentos');
    const select = document.getElementById('afast-colaborador');
    select.value = colaboradorId;
}

function abrirModalRetorno(afastamentoId, colaboradorId) {
    document.getElementById('retorno-afastamento-id').value = afastamentoId;
    document.getElementById('retorno-colaborador-id').value = colaboradorId;
    document.getElementById('retorno-data').value = obterDataHoje();
    abrirModal('modal-retorno');
}

async function confirmarRetornoAfastamento(e) {
    e.preventDefault();
    const afastamentoId = document.getElementById('retorno-afastamento-id').value;
    const colaboradorId = document.getElementById('retorno-colaborador-id').value;
    const dataRetorno = document.getElementById('retorno-data').value;

    try {
        const res = await fetch(`/api/afastamentos/${afastamentoId}/retorno`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ colaborador_id: colaboradorId, data_retorno: dataRetorno })
        });

        if (res.ok) {
            mostrarToast('Retorno registrado! Colaborador disponível.', 'success');
            fecharModal('modal-retorno');
            carregarAfastamentos();
            carregarColaboradores();
            carregarIndicadores();
        } else {
            const err = await res.json();
            mostrarToast(err.error || 'Erro ao registrar retorno', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de rede ao registrar retorno', 'error');
    }
}


// --- MODAL IMPORTAÇÃO EXCEL (botão do header) ---

function abrirModalImportarExcel() {
    document.getElementById('form-importar-excel').reset();
    document.getElementById('import-resultado').style.display = 'none';
    abrirModal('modal-importar-excel');
}

async function confirmarImportacaoExcel(e) {
    e.preventDefault();
    const inputArquivo = document.getElementById('excel-arquivo');
    const motivoAfastamento = document.getElementById('excel-motivo').value.trim();
    const btnSubmit = document.getElementById('btn-importar-submit');
    const panelResultado = document.getElementById('import-resultado');

    if (!inputArquivo.files || inputArquivo.files.length === 0) {
        mostrarToast('Selecione um arquivo de planilha', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', inputArquivo.files[0]);
    formData.append('motivo_afastamento', motivoAfastamento);

    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Processando...';

    try {
        const res = await fetch('/api/importar-excel', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            mostrarToast('Importação concluída!', 'success');
            panelResultado.style.display = 'block';
            panelResultado.innerHTML = `
                <h4><i class="fa-solid fa-square-check" style="color: var(--accent-green);"></i> Resultado da Importação:</h4>
                <ul>
                    <li><strong>Total de linhas lidas:</strong> ${data.total_linhas}</li>
                    <li><strong>Escalas criadas:</strong> ${data.escalas_criadas}</li>
                    <li><strong>Afastamentos por remoções de ajudante:</strong> ${data.afastamentos_gerados}</li>
                    ${data.erros > 0 ? `<li style="color: var(--accent-red);"><strong>Erros encontrados:</strong> ${data.erros}</li>` : ''}
                </ul>
            `;

            carregarEscalas();
            carregarColaboradores();
            carregarFrota();
            carregarRotas();
            carregarAfastamentos();
            carregarIndicadores();
            carregarHistorico();
        } else {
            mostrarToast(data.error || 'Erro na importação', 'error');
        }
    } catch (err) {
        mostrarToast('Erro de comunicação com o servidor', 'error');
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Processar Importação';
    }
}


// --- UTILITÁRIOS ---

function abrirModal(id) {
    document.getElementById(id).classList.add('active');
}

function fecharModal(id) {
    document.getElementById(id).classList.remove('active');
}

function obterDataHoje() {
    return new Date().toISOString().split('T')[0];
}

function formatarData(dataStr) {
    if (!dataStr) return '-';
    const partes = dataStr.split('T')[0].split('-');
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
        row.style.display = texto.includes(termo) ? '' : 'none';
    });
}

function mostrarToast(mensagem, tipo = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.innerHTML = `
        <i class="fa-solid ${tipo === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation'}"></i>
        <span>${mensagem}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ============================================================
// DROPDOWN DE AÇÕES
// ============================================================
function toggleActionsMenu(btn, event) {
    event.stopPropagation();

    // Fecha todos os outros menus abertos
    document.querySelectorAll('.actions-menu.open').forEach(menu => {
        if (menu !== btn.nextElementSibling) {
            menu.classList.remove('open');
        }
    });

    // Abre/fecha o menu clicado
    const menu = btn.nextElementSibling;
    menu.classList.toggle('open');
}

function fecharActionsMenu() {
    document.querySelectorAll('.actions-menu.open').forEach(menu => {
        menu.classList.remove('open');
    });
}

// Fecha o menu ao clicar fora
document.addEventListener('click', (e) => {
    if (!e.target.closest('.actions-dropdown')) {
        fecharActionsMenu();
    }
});