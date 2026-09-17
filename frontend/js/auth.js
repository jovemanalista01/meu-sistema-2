/**
 * LogiScale Web - Módulo de Autenticação e Controle de Acesso (RBAC)
 * Integra com Firebase Authentication e suporta perfil de desenvolvimento.
 */

class AuthService {
    constructor() {
        this.currentUser = null;
        this.authToken = null;
        this.firebaseAuth = null;
        this.listeners = [];
        this.inicializar();
    }

    inicializar() {
        // Tenta inicializar Firebase SDK se disponível
        if (typeof firebase !== "undefined" && window.APP_CONFIG && window.APP_CONFIG.FIREBASE_CONFIG.apiKey !== "AIzaSyDUMMY-REPLACE-WITH-YOUR-KEY") {
            try {
                if (!firebase.apps.length) {
                    firebase.initializeApp(window.APP_CONFIG.FIREBASE_CONFIG);
                }
                this.firebaseAuth = firebase.auth();
                this.firebaseAuth.onAuthStateChanged(async (user) => {
                    if (user) {
                        const token = await user.getIdToken();
                        // Busca dados e perfil do usuário
                        this.authToken = token;
                        this.currentUser = {
                            uid: user.uid,
                            email: user.email,
                            nome: user.displayName || user.email.split("@")[0],
                            role: "OPERACIONAL" // Padrão até validar na API
                        };

                        // Tenta obter o papel real na API
                        try {
                            const res = await fetch(`${window.APP_CONFIG.API_BASE_URL}/api/auth/me`, {
                                headers: { "Authorization": `Bearer ${token}` }
                            });
                            if (res.ok) {
                                const data = await res.json();
                                if (data.usuario && data.usuario.role) {
                                    this.currentUser.role = data.usuario.role;
                                }
                            }
                        } catch (e) {
                            console.warn("Não foi possível consultar perfil na API:", e);
                        }

                        this.salvarSessao();
                    } else {
                        this.limparSessao();
                    }
                    this.notificarMudanca();
                });
            } catch (err) {
                console.warn("Firebase Auth não configurado. Utilizando autenticação local/dev.", err);
            }
        }

        // Recupera sessão local salva caso não esteja usando Firebase ativo
        if (!this.currentUser) {
            this.recuperarSessaoLocal();
        }
    }

    recuperarSessaoLocal() {
        const saved = localStorage.getItem("LOGISCALE_AUTH_USER");
        const token = localStorage.getItem("LOGISCALE_AUTH_TOKEN");
        if (saved && token) {
            try {
                this.currentUser = JSON.parse(saved);
                this.authToken = token;
            } catch (e) {
                this.limparSessao();
            }
        }
    }

    salvarSessao() {
        if (this.currentUser) {
            localStorage.setItem("LOGISCALE_AUTH_USER", JSON.stringify(this.currentUser));
        }
        if (this.authToken) {
            localStorage.setItem("LOGISCALE_AUTH_TOKEN", this.authToken);
        }
    }

    limparSessao() {
        this.currentUser = null;
        this.authToken = null;
        localStorage.removeItem("LOGISCALE_AUTH_USER");
        localStorage.removeItem("LOGISCALE_AUTH_TOKEN");
    }

    onAuthStateChanged(callback) {
        this.listeners.push(callback);
        if (this.currentUser) {
            callback(this.currentUser);
        }
    }

    notificarMudanca() {
        this.listeners.forEach(cb => cb(this.currentUser));
        this.aplicarPermissoesUI();
    }

    async login(email, password) {
        // Se o Firebase estiver ativo e configurado
        if (this.firebaseAuth) {
            try {
                const userCredential = await this.firebaseAuth.signInWithEmailAndPassword(email, password);
                const token = await userCredential.user.getIdToken();
                this.authToken = token;
                return { success: true, user: userCredential.user };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }

        // Modo de Acesso Local / Demonstração (Permite testar imediatamente sem credenciais Firebase)
        const emailLower = email.toLowerCase().trim();
        let role = "OPERACIONAL";
        let nome = "Operador";

        if (emailLower.includes("admin") || password === "admin123") {
            role = "ADMIN";
            nome = "Administrador";
        }

        this.currentUser = {
            uid: "local-" + btoa(emailLower).slice(0, 8),
            email: emailLower,
            nome: nome,
            role: role
        };
        this.authToken = "dev-token-" + btoa(JSON.stringify(this.currentUser));
        this.salvarSessao();
        this.notificarMudanca();
        return { success: true, user: this.currentUser };
    }

    async logout() {
        if (this.firebaseAuth) {
            try {
                await this.firebaseAuth.signOut();
            } catch (e) {
                console.error(e);
            }
        }
        this.limparSessao();
        this.notificarMudanca();
    }

    getToken() {
        return this.authToken;
    }

    getUser() {
        return this.currentUser;
    }

    isAuthenticated() {
        return !!this.currentUser;
    }

    isAdmin() {
        return this.currentUser && this.currentUser.role === "ADMIN";
    }

    aplicarPermissoesUI() {
        const isAdmin = this.isAdmin();
        document.querySelectorAll('[data-role="admin"]').forEach(el => {
            el.style.display = isAdmin ? "" : "none";
        });

        const badgeUser = document.getElementById("user-role-badge");
        if (badgeUser && this.currentUser) {
            badgeUser.textContent = this.currentUser.role;
            badgeUser.className = `badge ${isAdmin ? "badge-admin" : "badge-operacional"}`;
        }

        const nomeUser = document.getElementById("user-display-name");
        if (nomeUser && this.currentUser) {
            nomeUser.textContent = this.currentUser.nome || this.currentUser.email;
        }
    }
}

window.authService = new AuthService();
