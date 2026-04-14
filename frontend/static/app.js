// Configuration - Load from config.js (loaded before this script) or use defaults
const config = {
    azureClientId: (typeof window !== 'undefined' && window.AZURE_CLIENT_ID) ? window.AZURE_CLIENT_ID : '',
    azureTenantId: (typeof window !== 'undefined' && window.AZURE_TENANT_ID) ? window.AZURE_TENANT_ID : '',
    apiBaseUrl: (() => {
        if (typeof window === 'undefined') return 'http://localhost:8000';
        if (typeof window.API_BASE_URL === 'string') {
            return window.API_BASE_URL.replace(/\/$/, '');
        }
        return 'http://localhost:8000';
    })(),
};

// MSAL Configuration (will be initialized if credentials are provided)
let msalInstance = null;
let msalConfig = null;

if (config.azureClientId && config.azureClientId !== '') {
    msalConfig = {
        auth: {
            clientId: config.azureClientId,
            authority: config.azureTenantId ? `https://login.microsoftonline.com/${config.azureTenantId}` : 'https://login.microsoftonline.com/common',
            redirectUri: window.location.origin
        },
        cache: {
            cacheLocation: "sessionStorage",
            storeAuthStateInCookie: false
        }
    };
    
    if (typeof msal !== 'undefined') {
        msalInstance = new msal.PublicClientApplication(msalConfig);
    }
}

// API Base URL
const API_BASE_URL = config.apiBaseUrl;

// Application State
let currentUser = null;
let conversationHistory = [];
let conversationId = null;
let currentHU = null;
let lastUserMessage = null;
let lastAssistantResponse = null;
let currentRating = null;

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const userInfo = document.getElementById('userInfo');
const requirementInput = document.getElementById('requirementInput');
const submitRequirementBtn = document.getElementById('submitRequirementBtn');
const requirementSection = document.getElementById('requirementSection');
const conversationSection = document.getElementById('conversationSection');
const chatMessages = document.getElementById('chatMessages');
const questionsContainer = document.getElementById('questionsContainer');
const questionsList = document.getElementById('questionsList');
const answerInput = document.getElementById('answerInput');
const submitAnswerBtn = document.getElementById('submitAnswerBtn');
const generateHUBtn = document.getElementById('generateHUBtn');
const reviewSection = document.getElementById('reviewSection');
const huPreview = document.getElementById('huPreview');
const approveHUBtn = document.getElementById('approveHUBtn');
const regenerateHUBtn = document.getElementById('regenerateHUBtn');
const successSection = document.getElementById('successSection');
const workItemId = document.getElementById('workItemId');
const workItemLink = document.getElementById('workItemLink');
const newRequirementBtn = document.getElementById('newRequirementBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const feedbackSection = document.getElementById('feedbackSection');
const starRating = document.getElementById('starRating');
const ratingText = document.getElementById('ratingText');
const isCorrectCheckbox = document.getElementById('isCorrectCheckbox');
const errorDescription = document.getElementById('errorDescription');
const correctionInput = document.getElementById('correctionInput');
const feedbackTextInput = document.getElementById('feedbackTextInput');
const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');

// Initialize MSAL and check authentication
async function initialize() {
    // Only initialize MSAL if client ID is configured and msal is available
    if (msalInstance && config.azureClientId && config.azureClientId !== '') {
        try {
            await msalInstance.initialize();
            
            const accounts = msalInstance.getAllAccounts();
            if (accounts.length > 0) {
                currentUser = accounts[0];
                updateAuthUI();
            } else {
                showLoginUI();
            }
        } catch (error) {
            console.error('MSAL initialization error:', error);
            // If MSAL fails, allow app to work without authentication
            showLoginUI();
        }
    } else {
        // MSAL not configured, allow app to work without authentication
        console.warn('MSAL not configured. App will work without authentication.');
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'none';
        userInfo.style.display = 'none';
    }
}

function showLoginUI() {
    loginBtn.style.display = 'block';
    logoutBtn.style.display = 'none';
    userInfo.style.display = 'none';
}

function updateAuthUI() {
    loginBtn.style.display = 'none';
    logoutBtn.style.display = 'block';
    userInfo.style.display = 'block';
    userInfo.innerHTML = `Bienvenido, ${currentUser.name || currentUser.username}`;
}

// Login
loginBtn.addEventListener('click', async () => {
    if (!msalInstance) {
        alert('MSAL no está configurado. Por favor, configura las credenciales de Azure AD.');
        return;
    }
    
    try {
        const loginRequest = {
            scopes: ['User.Read']
        };
        const response = await msalInstance.loginPopup(loginRequest);
        currentUser = response.account;
        updateAuthUI();
    } catch (error) {
        console.error('Login error:', error);
        alert('Error al iniciar sesión. Por favor, intenta nuevamente.');
    }
});

// Logout
logoutBtn.addEventListener('click', async () => {
    if (!msalInstance) {
        currentUser = null;
        showLoginUI();
        resetApp();
        return;
    }
    
    try {
        await msalInstance.logoutPopup();
        currentUser = null;
        showLoginUI();
        resetApp();
    } catch (error) {
        console.error('Logout error:', error);
    }
});

// Submit Requirement
submitRequirementBtn.addEventListener('click', async () => {
    const requirement = requirementInput.value.trim();
    if (!requirement) {
        alert('Por favor, ingresa un requerimiento.');
        return;
    }

    showLoading();
    conversationHistory = [{ role: 'user', content: requirement }];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/conversation/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                requirement: requirement,
                conversation_history: conversationHistory
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al procesar el requerimiento');
        }

        conversationId = data.conversation_id;
        
        // Show user message
        addMessageToChat('user', requirement);
        
        // Show related HUs if any
        if (data.related_hus && data.related_hus.length > 0) {
            showRelatedHUs(data.related_hus);
        }
        
        // Show system message
        addMessageToChat('system', data.message);
        
        // Show requirement section and conversation section
        requirementSection.style.display = 'none';
        conversationSection.style.display = 'block';
        
        // If there are questions, show them
        if (data.has_questions && data.questions && data.questions.length > 0) {
            showQuestions(data.questions);
        } else {
            // No questions, show generate button
            generateHUBtn.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Submit Answer
submitAnswerBtn.addEventListener('click', async () => {
    const answer = answerInput.value.trim();
    if (!answer) {
        alert('Por favor, ingresa una respuesta.');
        return;
    }

    showLoading();
    
    // Add answer to conversation history
    conversationHistory.push({ role: 'user', content: answer });
    addMessageToChat('user', answer);
    answerInput.value = '';

    try {
        const response = await fetch(`${API_BASE_URL}/api/conversation/continue`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                requirement: requirementInput.value.trim(),
                conversation_history: conversationHistory
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al procesar la respuesta');
        }

        conversationId = data.conversation_id;
        
        // Show system message
        addMessageToChat('system', data.message);
        
        // If there are more questions, show them
        if (data.has_questions && data.questions && data.questions.length > 0) {
            showQuestions(data.questions);
        } else {
            // No more questions, show generate button
            questionsContainer.style.display = 'none';
            generateHUBtn.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Generate HU
generateHUBtn.addEventListener('click', async () => {
    showLoading();
    
    // Store last user message for feedback
    lastUserMessage = requirementInput.value.trim();
    if (conversationHistory.length > 0) {
        const lastUserMsg = conversationHistory.filter(msg => msg.role === 'user').pop();
        if (lastUserMsg) {
            lastUserMessage = lastUserMsg.content;
        }
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/hu/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                requirement: requirementInput.value.trim(),
                conversation_history: conversationHistory,
                conversation_id: conversationId
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al generar la HU');
        }

        currentHU = data.hu_content;
        lastAssistantResponse = currentHU;
        displayHU(currentHU);
        
        // Hide conversation section and show review section
        conversationSection.style.display = 'none';
        reviewSection.style.display = 'block';
        
        // Reset feedback form
        resetFeedbackForm();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Approve and Create in Azure DevOps
approveHUBtn.addEventListener('click', async () => {
    if (!currentHU) {
        alert('No hay una HU para crear.');
        return;
    }

    showLoading();
    
    // Extract title from HU (first line after "1. Título de la HU")
    const lines = currentHU.split('\n');
    let title = 'Nueva Historia de Usuario';
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('Título de la HU') && i + 1 < lines.length) {
            title = lines[i + 1].replace(/^[-•]\s*/, '').trim();
            break;
        }
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/devops/create-work-item`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                hu_content: currentHU
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al crear el work item');
        }

        // Show success section
        reviewSection.style.display = 'none';
        successSection.style.display = 'block';
        workItemId.textContent = data.work_item_id;
        workItemLink.href = data.url;
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Regenerate HU
regenerateHUBtn.addEventListener('click', () => {
    reviewSection.style.display = 'none';
    conversationSection.style.display = 'block';
    generateHUBtn.click();
});

// New Requirement
newRequirementBtn.addEventListener('click', () => {
    resetApp();
});

// Helper Functions
function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showRelatedHUs(relatedHUs) {
    if (!relatedHUs || relatedHUs.length === 0) return;
    
    const relatedDiv = document.createElement('div');
    relatedDiv.className = 'related-hus';
    relatedDiv.innerHTML = `
        <h3>📚 HUs Relacionadas Encontradas</h3>
        <ul>
            ${relatedHUs.map(hu => `
                <li>
                    <div class="hu-title">${hu.title}</div>
                    <div class="hu-meta">
                        <span class="hu-relevance">${Math.round(hu.relevance * 100)}% relevante</span>
                        ${hu.work_item_id ? `Work Item #${hu.work_item_id}` : ''}
                        ${hu.common_keywords ? ` · Keywords: ${hu.common_keywords.slice(0, 3).join(', ')}` : ''}
                    </div>
                    ${hu.work_item_url ? `<a href="${hu.work_item_url}" target="_blank" style="font-size: 12px; color: #15601d;">Ver en Azure DevOps →</a>` : ''}
                </li>
            `).join('')}
        </ul>
    `;
    chatMessages.appendChild(relatedDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showQuestions(questions) {
    questionsList.innerHTML = '';
    questions.forEach(question => {
        const li = document.createElement('li');
        li.textContent = question;
        questionsList.appendChild(li);
    });
    questionsContainer.style.display = 'block';
    generateHUBtn.style.display = 'none';
}

function displayHU(huContent) {
    // Use the 'marked' library for robust Markdown → HTML conversion
    const markedLib = (typeof marked !== 'undefined') ? marked : null;
    const parseFn = markedLib
        ? (markedLib.parse ? markedLib.parse.bind(markedLib) : (typeof markedLib === 'function' ? markedLib : null))
        : null;

    if (parseFn) {
        // Configure marked — use .use() for v12+, fall back to .setOptions()
        try {
            if (markedLib.use) {
                markedLib.use({ breaks: true, gfm: true });
            } else if (markedLib.setOptions) {
                markedLib.setOptions({ breaks: true, gfm: true });
            }
        } catch (e) {
            console.warn('marked config warning:', e);
        }

        const html = parseFn(huContent);
        huPreview.innerHTML = '<div class="hu-content">' + html + '</div>';
    } else {
        // Fallback: simple manual conversion if marked didn't load
        let html = huContent;

        // Escape HTML entities first
        const tmp = document.createElement('div');
        tmp.textContent = html;
        html = tmp.innerHTML;

        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Bullet lists
        html = html.replace(/^[-•*]\s+(.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, (m) => '<ul>' + m + '</ul>');

        // Numbered lists
        html = html.replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        huPreview.innerHTML = '<div class="hu-content"><p>' + html + '</p></div>';
    }

    // If there are mermaid blocks, try to render them
    const mermaidEls = huPreview.querySelectorAll('code.language-mermaid');
    if (mermaidEls.length > 0) {
        const loadAndRender = () => {
            if (typeof mermaid !== 'undefined') {
                mermaid.initialize({ startOnLoad: false });
                mermaidEls.forEach((el, i) => {
                    const container = document.createElement('div');
                    container.className = 'mermaid';
                    container.textContent = el.textContent;
                    el.closest('pre').replaceWith(container);
                });
                mermaid.init(undefined, '.mermaid');
            }
        };

        if (typeof mermaid !== 'undefined') {
            loadAndRender();
        } else {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
            script.onload = loadAndRender;
            document.head.appendChild(script);
        }
    }
}

function resetApp() {
    requirementInput.value = '';
    conversationHistory = [];
    conversationId = null;
    currentHU = null;
    lastUserMessage = null;
    lastAssistantResponse = null;
    currentRating = null;
    chatMessages.innerHTML = '';
    questionsContainer.style.display = 'none';
    generateHUBtn.style.display = 'none';
    
    requirementSection.style.display = 'block';
    conversationSection.style.display = 'none';
    reviewSection.style.display = 'none';
    successSection.style.display = 'none';
    
    resetFeedbackForm();
}

function resetFeedbackForm() {
    currentRating = null;
    updateStarRating(0);
    isCorrectCheckbox.checked = false;
    errorDescription.value = '';
    correctionInput.value = '';
    feedbackTextInput.value = '';
}

function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Star Rating functionality
starRating.addEventListener('click', (e) => {
    if (e.target.classList.contains('star')) {
        const rating = parseInt(e.target.dataset.rating);
        currentRating = rating;
        updateStarRating(rating);
    }
});

function updateStarRating(rating) {
    const stars = starRating.querySelectorAll('.star');
    const ratings = ['Muy mala', 'Mala', 'Regular', 'Buena', 'Excelente'];
    
    stars.forEach((star, index) => {
        if (index < rating) {
            star.style.opacity = '1';
            star.style.transform = 'scale(1.2)';
        } else {
            star.style.opacity = '0.3';
            star.style.transform = 'scale(1)';
        }
    });
    
    ratingText.textContent = rating > 0 ? `Calificación: ${rating}/5 - ${ratings[rating - 1]}` : 'Selecciona una calificación';
}

// Submit Feedback
submitFeedbackBtn.addEventListener('click', async () => {
    if (!conversationId) {
        alert('No hay una conversación activa para calificar.');
        return;
    }

    if (!lastUserMessage || !lastAssistantResponse) {
        alert('No hay información suficiente para enviar feedback.');
        return;
    }

    const feedbackData = {
        conversation_id: conversationId,
        user_message: lastUserMessage,
        assistant_response: lastAssistantResponse,
        rating: currentRating,
        is_correct: isCorrectCheckbox.checked ? true : (currentRating && currentRating >= 4 ? true : null),
        error_description: errorDescription.value.trim() || null,
        correction: correctionInput.value.trim() || null,
        feedback_text: feedbackTextInput.value.trim() || null,
        hu_generated: currentHU || null
    };

    // Si no hay rating ni comentarios, pedir al menos un rating
    if (!currentRating && !feedbackData.error_description && !feedbackData.correction && !feedbackData.feedback_text) {
        alert('Por favor, proporciona al menos una calificación o comentario.');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/feedback/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Error al enviar feedback');
        }

        alert('¡Gracias por tu feedback! Tus comentarios nos ayudan a mejorar el sistema.');
        
        // Reset feedback form but keep it visible
        resetFeedbackForm();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al enviar feedback: ${error.message}`);
    } finally {
        hideLoading();
    }
});

// Initialize app
initialize();

