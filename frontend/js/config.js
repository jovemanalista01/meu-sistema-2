/**
 * LogiScale Web - Configuração do Cliente Frontend
 * Preparado para execução local ou hospedagem na Netlify.
 */

// Permite sobrescrever a URL da API via localStorage (ex: apontar para servidor em nuvem)
const savedApiUrl = localStorage.getItem("LOGISCALE_API_URL");

// Se estiver rodando na mesma porta/origem do Flask, usa caminho relativo "";
// Se estiver rodando em porta diferente ou Netlify sem backend local, usa a URL salva ou padrão local.
let defaultBaseUrl = "";
if (window.location.protocol === "file:") {
    defaultBaseUrl = "http://localhost:5000";
} else if (window.location.hostname === "localhost" && window.location.port !== "5000") {
    defaultBaseUrl = "http://localhost:5000";
}

window.APP_CONFIG = {
    // URL Base da API Flask
    API_BASE_URL: savedApiUrl || defaultBaseUrl,

    // Configuração pública do Firebase Web Client (APENAS chaves públicas do cliente web)
    // NUNCA coloque service_account.json ou private_key aqui!
    FIREBASE_CONFIG: {
        apiKey: "AIzaSyDUMMY-REPLACE-WITH-YOUR-KEY",
        authDomain: "logiscale-app.firebaseapp.com",
        projectId: "logiscale-app",
        storageBucket: "logiscale-app.appspot.com",
        messagingSenderId: "123456789012",
        appId: "1:123456789012:web:abcdef123456"
    },

    // Versão da aplicação
    VERSION: "2.0.0",

    // Atualiza dinamicamente a URL da API
    setApiUrl: function(newUrl) {
        if (newUrl) {
            localStorage.setItem("LOGISCALE_API_URL", newUrl.trim().replace(/\/$/, ""));
        } else {
            localStorage.removeItem("LOGISCALE_API_URL");
        }
        window.location.reload();
    }
};
