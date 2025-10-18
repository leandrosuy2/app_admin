// Obtém o sessionId diretamente da URL
const sessionId = window.location.pathname.split('/').pop();

// Função para buscar contatos e mensagens da sessão
async function fetchMessages() {
  const response = await fetch(`/messages/${sessionId}`);
  if (response.ok) {
    const data = await response.json();
    return data.contacts;
  } else {
    console.error('Erro ao buscar mensagens:', response.statusText);
    return [];
  }
}

// Renderiza a lista de contatos
function renderContacts(contacts) {
  const contactsContainer = document.getElementById('contacts');
  contactsContainer.innerHTML = contacts
    .map(contact => `<div class="contact" data-contact="${contact.contact}">${contact.contact}</div>`)
    .join('');
}

// Renderiza as mensagens de um contato
function renderMessages(contactName, messages) {
  const chatHeader = document.getElementById('chat-header');
  const messagesContainer = document.getElementById('messages');

  chatHeader.textContent = contactName; // Exibe o nome do contato no cabeçalho
  messagesContainer.innerHTML = messages
    .map(
      message => `
        <div class="message ${message.direction}">
          <div>${message.content}</div>
          <div class="timestamp">${message.timestamp}</div>
        </div>
      `
    )
    .join('');
}


// Configura os cliques nos contatos para exibir mensagens
function setupContactClick(contacts) {
  const contactElements = document.querySelectorAll('.contact');
  contactElements.forEach(contactElement => {
    contactElement.addEventListener('click', () => {
      const contactName = contactElement.dataset.contact;
      const contact = contacts.find(c => c.contact === contactName);
      renderMessages(contactName, contact.messages);
    });
  });
}

// Inicializa a interface
async function init() {
  const contacts = await fetchMessages();
  renderContacts(contacts);
  setupContactClick(contacts);
}

init();
