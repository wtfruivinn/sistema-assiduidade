
// ============================================================
// validacao.js — Lógica do frontend da aula
// Sistema de Assiduidade — Universidade Zambeze
// ============================================================
 
// Obter CSRF token
function getCookie(name) {
    let value = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(c => {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                value = decodeURIComponent(c.substring(name.length + 1));
            }
        });
    }
    return value;
}
 
const CSRF = getCookie('csrftoken');
const AULA_ID = window.location.pathname.split('/')[2];
 
// Função auxiliar: POST
// Nunca lança erro: se o servidor falhar (500, 403, resposta não-JSON),
// devolve {erro: "..."} para os restantes blocos tratarem.
async function post(url, formData) {
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': CSRF},
            body: formData
        });
 
        let dados = null;
        try {
            dados = await r.json();
        } catch (e) {
            // resposta não é JSON (ex.: página de erro do Django)
        }
 
        if (!r.ok) {
            const msg = (dados && (dados.erro || dados.mensagem)) ||
                        `Erro do servidor (${r.status}). Veja o terminal do runserver.`;
            console.error('POST falhou:', url, r.status, dados);
            return {...(dados || {}), sucesso: false, erro: msg};
        }
 
        return dados || {sucesso: false, erro: 'Resposta inválida do servidor.'};
    } catch (e) {
        console.error('Erro de rede:', url, e);
        return {sucesso: false, erro: 'Sem ligação ao servidor.'};
    }
}
 
// ============================================================
// 1. INICIAR AULA
// ============================================================
const btnIniciar = document.getElementById('btn-iniciar');
if (btnIniciar) {
    btnIniciar.onclick = async () => {
        btnIniciar.disabled = true;
        btnIniciar.innerHTML = '<i class="bi bi-hourglass-split"></i> A iniciar...';
        const d = await post(`/ajax/aula/${AULA_ID}/iniciar/`, new FormData());
        if (d.sucesso) {
            location.reload();
        } else {
            alert('❌ ' + (d.erro || 'Erro ao iniciar.'));
            btnIniciar.disabled = false;
            btnIniciar.innerHTML = '<i class="bi bi-play-circle"></i> Iniciar Aula';
        }
    };
}
 
// ============================================================
// 2. VALIDAR COM GPS
// ============================================================
const btnGPS = document.getElementById('btn-validar-gps');
if (btnGPS) {
    btnGPS.onclick = () => {
        if (!navigator.geolocation) {
            alert('❌ Browser não suporta geolocalização.');
            return;
        }
        btnGPS.disabled = true;
        btnGPS.innerHTML = '<i class="bi bi-hourglass-split"></i> A obter localização...';
 
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const fd = new FormData();
                fd.append('latitude', pos.coords.latitude);
                fd.append('longitude', pos.coords.longitude);
                fd.append('precisao', pos.coords.accuracy);
                const d = await post(`/ajax/aula/${AULA_ID}/validar/`, fd);
                mostrarResultadoValidacao(d);
                btnGPS.disabled = false;
                btnGPS.innerHTML = '<i class="bi bi-geo-alt"></i> Validar com GPS';
            },
            (erro) => {
                let msg = 'Erro ao obter localização.';
                if (erro.code === 1) msg = '❌ Permissão de localização negada.';
                if (erro.code === 2) msg = '❌ Localização indisponível.';
                if (erro.code === 3) msg = '❌ Tempo esgotado.';
                alert(msg);
                btnGPS.disabled = false;
                btnGPS.innerHTML = '<i class="bi bi-geo-alt"></i> Validar com GPS';
            },
            {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
        );
    };
}
 
// ============================================================
// 3. VALIDAR COM CÂMARA (ler QR Code)
// ============================================================
const btnQRCamera = document.getElementById('btn-validar-qr-camera');
if (btnQRCamera) {
    let scannerAtivo = false;
 
    btnQRCamera.onclick = () => {
        const qrReader = document.getElementById('qr-reader');
        if (!scannerAtivo) {
            qrReader.style.display = 'block';
            btnQRCamera.innerHTML = '<i class="bi bi-x-circle"></i> Fechar Câmara';
 
            const html5QrCode = new Html5Qrcode("qr-reader");
            html5QrCode.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: 250 },
                async (textoLido) => {
                    // QR lido com sucesso — parar câmara
                    await html5QrCode.stop();
                    qrReader.style.display = 'none';
                    scannerAtivo = false;
                    btnQRCamera.innerHTML = '<i class="bi bi-camera"></i> Ler QR com Câmara';
 
                    // Enviar para API
                    const fd = new FormData();
                    fd.append('qr_code', textoLido);
                    const d = await post(`/ajax/aula/${AULA_ID}/validar/`, fd);
                    mostrarResultadoValidacao(d);
                },
                (erro) => { /* erros de leitura são normais */ }
            ).catch(err => {
                alert('❌ Não foi possível aceder à câmara: ' + err);
                qrReader.style.display = 'none';
                scannerAtivo = false;
                btnQRCamera.innerHTML = '<i class="bi bi-camera"></i> Ler QR com Câmara';
            });
 
            scannerAtivo = true;
        } else {
            qrReader.style.display = 'none';
            btnQRCamera.innerHTML = '<i class="bi bi-camera"></i> Ler QR com Câmara';
            scannerAtivo = false;
        }
    };
}
 
// ============================================================
// 4. VALIDAR COM QR MANUAL (input de texto)
// ============================================================
const btnQRManual = document.getElementById('btn-validar-qr-manual');
if (btnQRManual) {
    btnQRManual.onclick = async () => {
        const qr = document.getElementById('qr-input').value.trim();
        if (!qr) return alert('Insira o código QR.');
        const fd = new FormData();
        fd.append('qr_code', qr);
        const d = await post(`/ajax/aula/${AULA_ID}/validar/`, fd);
        mostrarResultadoValidacao(d);
    };
}
 
// ============================================================
// Mostrar resultado da validação
// ============================================================
function mostrarResultadoValidacao(d) {
    const resultado = document.getElementById('resultado-validacao');
    if (!resultado) return;
 
    if (d.resultado === 'autorizado') {
        resultado.innerHTML = `
            <div class="alert alert-success">
                <i class="bi bi-check-circle-fill"></i>
                <strong>Localização Validada!</strong><br>
                ${d.mensagem}
            </div>`;
    } else if (!d.resultado) {
        // Erro técnico (500, rede, etc.) — não é um bloqueio real
        resultado.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <strong>Erro</strong><br>
                ${d.erro || d.mensagem || 'Não foi possível validar.'}
            </div>`;
         } else if (d.bloqueada) {
        resultado.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-octagon-fill"></i>
                <strong>🚫 AULA BLOQUEADA</strong><br>
                ${(d.mensagem || '').replace(/\n/g, '<br>')}
            </div>`;
        // Recarregar para mostrar o formulário de revisão
        setTimeout(() => location.reload(), 3000);
    } else {
        // Falhou, mas ainda tem tentativas
        resultado.innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <strong>Não validado</strong><br>
                ${(d.mensagem || '').replace(/\n/g, '<br>')}
            </div>`;
    }
}
 
// ============================================================
// 5. GUARDAR PRESENÇAS
// ============================================================
const btnPres = document.getElementById('btn-guardar-presencas');
if (btnPres) {
    btnPres.onclick = async () => {
        btnPres.disabled = true;
        btnPres.innerHTML = '<i class="bi bi-hourglass-split"></i> A guardar...';
        const fd = new FormData();
        document.querySelectorAll('input[type="radio"]:checked').forEach(r => fd.append(r.name, r.value));
        const d = await post(`/ajax/aula/${AULA_ID}/presencas/`, fd);
        alert(d.mensagem || d.erro);
        btnPres.disabled = false;
        btnPres.innerHTML = '<i class="bi bi-save"></i> Guardar Presenças';
    };
}
 
// ============================================================
// 6. ENCERRAR AULA
// ============================================================
const btnEnc = document.getElementById('btn-encerrar');
if (btnEnc) {
    btnEnc.onclick = async () => {
        const sumario = document.getElementById('sumario').value.trim();
        const tema = document.getElementById('tema').value.trim();
        if (!sumario || !tema) return alert('❌ Preencha o sumário e o tema.');
        if (!confirm('Tem a certeza que quer encerrar a aula?')) return;
 
        btnEnc.disabled = true;
        btnEnc.innerHTML = '<i class="bi bi-hourglass-split"></i> A encerrar...';
 
        const fd = new FormData();
        fd.append('sumario', sumario);
        fd.append('tema', tema);
        const d = await post(`/ajax/aula/${AULA_ID}/encerrar/`, fd);
 
        const resultado = document.getElementById('resultado-encerrar');
        if (d.sucesso) {
            resultado.innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="bi bi-check-circle"></i> Aula Validada!</h5>
                    <p class="mb-1"><strong>Horas:</strong> ${d.horas}h</p>
                    <p class="mb-1"><strong>Valor/hora:</strong> ${d.valor_hora} MT</p>
                    <p class="mb-0"><strong>Total a pagar:</strong> <span class="fs-4">${d.valor_total} MT</span></p>
                    ${d.pendente ? `<hr><p class="mb-0 text-warning-emphasis"><i class="bi bi-hourglass-split"></i> ${d.mensagem}</p>` : ''}
                </div>`;
            setTimeout(() => location.href = '/painel/', 3000);
        } else {
            alert('❌ ' + (d.erro || 'Erro ao encerrar.'));
            btnEnc.disabled = false;
            btnEnc.innerHTML = '<i class="bi bi-stop-circle"></i> Encerrar e Validar Aula';
        }
    };
}
 
console.log('✅ validacao.js carregado');
 
// ============================================================
// 7. PEDIR REVISÃO (aula bloqueada)
// ============================================================
const btnRevisao = document.getElementById('btn-pedir-revisao');
if (btnRevisao) {
    btnRevisao.onclick = async () => {
        const motivo = document.getElementById('motivo-revisao').value.trim();
        if (motivo.length < 10) return alert('❌ Explique o motivo (mínimo 10 caracteres).');

        btnRevisao.disabled = true;
        const fd = new FormData();
        fd.append('motivo', motivo);
        const d = await post(`/ajax/aula/${AULA_ID}/pedir-revisao/`, fd);
        if (d.sucesso) {
            alert(d.mensagem);
            location.reload();
        } else {
            alert('❌ ' + (d.erro || 'Erro ao enviar o pedido.'));
            btnRevisao.disabled = false;
        }
    };
}