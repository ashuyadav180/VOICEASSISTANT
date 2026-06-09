const orb = document.getElementById('siri-orb');
const statusText = document.getElementById('status-text');
const transcript = document.getElementById('transcript');
const commandInput = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');

let ws;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        addSystemMessage("Connected to SIRI core.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'state') {
            updateState(data.state);
        } else if (data.type === 'transcript') {
            addMessage(data.role, data.text);
        }
    };

    ws.onclose = () => {
        updateState('offline');
        addSystemMessage("Connection lost. Reconnecting in 3s...");
        setTimeout(connectWebSocket, 3000);
    };
}

function updateState(state) {
    orb.className = 'orb';
    statusText.textContent = state.toUpperCase();
    
    if (state === 'offline') {
        orb.classList.add('state-sleeping');
        return;
    }
    
    orb.classList.add(`state-${state}`);
}

function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    // Simple markdown link parser
    let htmlText = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:#60a5fa">$1</a>');
    // Convert newlines to breaks
    htmlText = htmlText.replace(/\n/g, '<br>');
    div.innerHTML = htmlText;
    
    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
}

function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = text;
    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
}

function sendCommand() {
    const text = commandInput.value.trim();
    if (text && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'process_text', text: text }));
        // addMessage('user', text); // backend broadcasts user transcript too
        commandInput.value = '';
    }
}

sendBtn.addEventListener('click', sendCommand);
commandInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendCommand();
});

connectWebSocket();
