// Simple polling script for chat auto-refresh
// Improved polling script for chat auto-refresh
setInterval(function() {
    fetch(window.location.pathname, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
        .then(response => response.text())
        .then(html => {
            let parser = new DOMParser();
            let doc = parser.parseFromString(html, 'text/html');
            let newChat = doc.body.firstElementChild;
            let oldChat = document.querySelector('#chat-messages');
            if (newChat && oldChat) {
                oldChat.innerHTML = newChat.innerHTML;
            }
        });
}, 1000); // Poll every 1 second    
