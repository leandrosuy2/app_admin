const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const express = require('express');
const mysql = require('mysql2/promise');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const app = express();
app.use(express.json());
const port = 8012;

const sessions = {};

const dbConfig = {
  host: '127.0.0.1',
  user: 'root',
  password: '@Intercheck!#jksddfofsmdçls$',
  database: 'app_sistnortecheck',
  waitForConnections: true,
  connectionLimit: 100,
  queueLimit: 0,
};

let sessionIndex = 0
const holidays = [
  '2024-01-01', // Ano Novo
  '2024-02-12', // Carnaval
  '2024-02-13', // Quarta-feira de Cinzas (ponto facultativo até as 14h)
  '2024-03-29', // Sexta-feira Santa
  '2024-04-21', // Tiradentes
  '2024-05-01', // Dia do Trabalho
  '2024-05-30', // Corpus Christi
  '2024-09-07', // Independência do Brasil
  '2024-10-12', // Nossa Senhora Aparecida
  '2024-11-02', // Finados
  '2024-11-15', // Proclamação da República
  '2024-12-25'  // Natal
];

function isHoliday(date) {
  const formattedDate = date.toISOString().split('T')[0];
  return holidays.includes(formattedDate);
}

function isWorkingHours() {
  const now = new Date();
  const dayOfWeek = now.getDay(); // 0 = domingo, 6 = sábado
  const hour = now.getHours();
  const minute = now.getMinutes();

  if (dayOfWeek === 0 || dayOfWeek === 6 || isHoliday(now)) {
    return false; // Feriado ou fim de semana
  }

  const currentTimeInMinutes = hour * 60 + minute;
  const startTimeInMinutes = 9 * 60; // 14:00
  const endTimeInMinutes = 17 * 60 + 59; // 17:59

  return currentTimeInMinutes >= startTimeInMinutes && currentTimeInMinutes <= endTimeInMinutes;
}


function getActiveSessions() {
  return Object.keys(sessions).filter(sessionId => sessions[sessionId].isConnected);
}


const pool = mysql.createPool(dbConfig);

app.use(express.static(path.join(__dirname, 'public')));

async function fetchContactsToSend() {
  const connection = await pool.getConnection();
  try {
    const [contacts] = await connection.execute(`
      SELECT DISTINCT
        devedores.id,
        titulo.data_envio_whatsapp,
        titulo.dataVencimento,
        t.telefone,
        devedores.nome,
        titulo.statusBaixa,
        titulo.data_baixa,
        core_empresa.nome_fantasia,
        devedores.nome as DevedorNome,
        core_empresa.nome_fantasia AS EmpresaNomeFantasia,
        titulo.valor AS ParcelaValor,
        titulo.dataVencimento AS VencimentoParcela,
        core_empresa.banco AS ChavePix
      FROM (
        SELECT id, telefone FROM devedores UNION ALL
        SELECT id, telefone1 FROM devedores UNION ALL
        SELECT id, telefone2 FROM devedores UNION ALL
        SELECT id, telefone3 FROM devedores UNION ALL
        SELECT id, telefone4 FROM devedores UNION ALL
        SELECT id, telefone5 FROM devedores UNION ALL
        SELECT id, telefone6 FROM devedores UNION ALL
        SELECT id, telefone7 FROM devedores UNION ALL
        SELECT id, telefone8 FROM devedores UNION ALL
        SELECT id, telefone9 FROM devedores UNION ALL
        SELECT id, telefone10 FROM devedores
      ) t
      JOIN devedores ON t.id = devedores.id
      JOIN core_empresa ON devedores.empresa_id = core_empresa.id
      JOIN titulo ON titulo.devedor_id = devedores.id
      WHERE
        titulo.statusBaixa = 3
        AND titulo.dataVencimento < CURDATE()
        AND (titulo.data_envio_whatsapp < CURDATE() OR titulo.data_envio_whatsapp IS NULL)
        AND t.telefone IS NOT NULL
        AND t.telefone <> ''     
        AND titulo.data_baixa IS NULL
        AND titulo.dataVencimento < CURDATE() 
        ORDER BY titulo.data_envio_whatsapp ASC
    `);

    const contactMap = contacts.reduce((acc, contact) => {
      const formattedPhone = contact.telefone.replace(/\D/g, ''); // Remove caracteres não numéricos

      if (formattedPhone.length > 0) {
        if (!acc[contact.id]) {
          acc[contact.id] = {
            ...contact,
            telefones: [],
          };
        }

        // Adiciona "55" se não estiver presente e verifica se há 13 dígitos
        let phone = formattedPhone.startsWith('55') ? formattedPhone : `55${formattedPhone}`;
        
        // Remove o quinto dígito se o número tiver 13 dígitos
        if (phone.length === 13) {
          phone = phone.slice(0, 4) + phone.slice(5);
        }

        acc[contact.id].telefones.push(phone);
      }
      return acc;
    }, {});

    return Object.values(contactMap); // Transforma o dicionário em uma lista de contatos
  } finally {
    connection.release();
  }
}





function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


// Função para aguardar por um intervalo aleatório de tempo e exibir no log
function randomDelay() {
    const delays = [15000, 30000, 50000, 80000, 60000, 90000, 180000, 150000, 130000, 20000, 220000, 250000, 300000, 45000, 100000, 105000, 5000];
    const randomIndex = Math.floor(Math.random() * delays.length);
    const delay = delays[randomIndex];
    console.log(`Aguardando ${delay / 1000} segundos para enviar a próxima mensagem...`);
    return delay;
}


const sentConfirmations = new Set(); // Conjunto para rastrear mensagens de confirmação enviadas


// Uso na função principal para aguardar e logar o tempo restante
async function sendPersonalMessage(sock, contact) {
    if (!isWorkingHours()) {
        console.log('Fora do horário de envio ou dia não útil. Pulando...');
        return;
    }

    for (const telefone of contact.telefones) {
        // Verifica se o número já foi processado
        if (sentConfirmations.has(telefone)) {
            console.log(`Mensagem já enviada para o número: ${telefone}. Pulando...`);
            continue;
        }

        console.log(`Processando contato: ${contact.DevedorNome}, telefone: ${telefone}`);

        // Busca as parcelas em atraso
        const overdueInstallments = await fetchOverdueInstallments(contact.id);

        // Formata o texto das parcelas em atraso
        const installmentsText = overdueInstallments.length > 0
            ? `⚠️ *Parcelas em atraso:*\n${overdueInstallments.map(installment => {
                return `   - 💰 *Valor:* R$ ${installment.valor.toFixed(2)} | 📅 *Vencimento:* ${formatDate(installment.dataVencimento)}`;
            }).join('\n')}`
            : '⚠️ *Parcelas em atraso:*\n   - Nenhuma parcela encontrada.';

        // Envia mensagem de confirmação
        const confirmationMessage = `
            Olá, tudo bem?
            Somos do escritório Adv Assessoria. Neste contato, eu falo com Sr(a) ${contact.DevedorNome}?

            Por favor, responda com:
            1️⃣ Sim  
            2️⃣ Não
        `;
        await sock.sendMessage(telefone + '@s.whatsapp.net', { text: confirmationMessage });
        console.log(`Mensagem de confirmação enviada para ${telefone}`);

        // Adiciona o número ao conjunto de rastreamento
        sentConfirmations.add(telefone);

        // Aguarda a resposta do usuário
        const response = await waitForResponse(sock, telefone);

        if (response === '1') {
            // Envia mensagem personalizada após confirmação
            const personalizedMessage = `
                🌟 *Olá ${contact.DevedorNome || 'Sr(a)'},* 🌟

                🙋‍♀️ *Me chamo Cristina* e tenho uma mensagem importante para você.

                ⚠️ *Lamentamos que não tenha pago a(s) seguinte(s) parcela(s) referente ao acordo firmado junto à empresa:*  
                📌 *${contact.EmpresaNomeFantasia || 'N/A'}*

                ${installmentsText}

                🔑 *Solicite a CHAVE PIX ou boleto para regularização:*  

                ❗ *Solicitamos sua imediata atenção!*  
                Hoje seu acordo está sendo encaminhado para:
                - ❌ *Negativação junto aos órgãos de proteção ao crédito (SPC/SERASA/BOA VISTA)*  
                - ⚖️ *Sujeito a análise e acionamento jurídico junto à comarca de sua cidade.*

                📲 *Negocie aqui pelo WhatsApp ou na loja:*  
                🏢 *${contact.EmpresaNomeFantasia || 'N/A'}*

                🖋️ *Caso já tenha realizado o pagamento, por gentileza desconsiderar a mensagem*
                --- 
                ⚠️ *Estamos à disposição para ajudar!*  
                📞 *Entre em contato conosco.*

                🔹 *Atenciosamente,*  
                🖋️ *Escritório Jurídico*  
                ⚖️ *Adv Assessoria & Associados*
            `;
            await sock.sendMessage(telefone + '@s.whatsapp.net', { text: personalizedMessage });
            console.log(`Mensagem personalizada enviada para ${telefone}`);
            await updateContactAsMessaged(contact.id); // Atualiza o banco de dados
        } else if (response === '2') {
            const apologyMessage = `
                Obrigado por nos informar. Vamos registrar sua solicitação e remover seu número de nosso banco de dados.
            `;
            await sock.sendMessage(telefone + '@s.whatsapp.net', { text: apologyMessage });
            console.log(`Mensagem de remoção enviada para ${telefone}`);
        } else {
            console.log(`Nenhuma resposta válida recebida de ${telefone}.`);
        }

        // Aguarda um intervalo aleatório antes de continuar
        const delay = randomDelay();
        console.log(`Aguardando ${delay / 1000} segundos antes de prosseguir...`);
        await new Promise(resolve => setTimeout(resolve, delay));
    }
}



async function sendMessagesRoundRobin() {
    const activeSessions = getActiveSessions();

    if (activeSessions.length === 0) {
        console.log('Nenhuma sessão ativa para envio.');
        return;
    }

    const contacts = await fetchContactsToSend();

    for (const contact of contacts) {
        if (!isWorkingHours()) {
            console.log('Fora do horário de envio ou dia não útil. Pulando...');
            break; // Interrompe o envio se não estiver no horário ou for dia não útil
        }

        const sessionId = activeSessions[sessionIndex];
        const sock = sessions[sessionId].sock;

        await sendPersonalMessage(sock, contact); // Processa o contato atual

        // Avança para a próxima sessão no rodízio
        sessionIndex = (sessionIndex + 1) % activeSessions.length;
    }
}

// Função para aguardar a resposta do usuário
async function waitForResponse(sock, telefone) {
    return new Promise((resolve) => {
        const messageHandler = (upsert) => {
            const messages = upsert.messages;
            for (const msg of messages) {
                const remoteJid = msg.key.remoteJid;
                const conversation = msg.message?.conversation;

                if (remoteJid === telefone + '@s.whatsapp.net' && conversation) {
                    const text = conversation.trim();
                    console.log(`Resposta recebida do número ${telefone}: ${text}`);

                    if (text === '1' || text === '2') {
                        sock.ev.off('messages.upsert', messageHandler);
                        resolve(text);
                    }
                }
            }
        };

        sock.ev.on('messages.upsert', messageHandler);
    });
}





// Função para remover contato do banco de dados
async function removeContact(contactId) {
  const connection = await pool.getConnection();
  try {
    await connection.execute(
      `DELETE FROM devedores WHERE id = ?`,
      [contactId]
    );
  } finally {
    connection.release();
  }
}

function formatDate(date) {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0'); // Dia com dois dígitos
    const month = String(d.getMonth() + 1).padStart(2, '0'); // Mês com dois dígitos
    const year = d.getFullYear(); // Ano com quatro dígitos
    return `${day}/${month}/${year}`; // Formato DD/MM/YYYY
}

async function fetchOverdueInstallments(devedorId) {
    const connection = await pool.getConnection();
    try {
        const [installments] = await connection.execute(`
            SELECT valor, dataVencimento 
            FROM titulo 
            WHERE devedor_id = ? 
            AND dataVencimento < CURDATE() 
            AND statusBaixa = 3 AND idTituloRef IS NOT NULL
        `, [devedorId]);

        return installments; // Sempre retorna uma lista, mesmo que vazia
    } finally {
        connection.release();
    }
}




async function updateContactAsMessaged(contactId) {
  const connection = await pool.getConnection();
  try {
    const now = new Date();
    const formattedDate = now.toISOString().split('T')[0]; // Garante o formato YYYY-MM-DD

    const [result] = await connection.execute(
      "UPDATE titulo SET data_envio_whatsapp = ? WHERE devedor_id = ?",
      [formattedDate, contactId]
    );

    if (result.affectedRows === 0) {
      console.log(`Nenhuma linha atualizada para o devedor ID: ${contactId}. Verifique se o ID existe.`);
    } else {
      console.log(`Data de envio atualizada para o devedor ID: ${contactId}.`);
    }
  } catch (error) {
    console.error(`Erro ao atualizar data_envio_whatsapp para o devedor ID: ${contactId}:`, error);
  } finally {
    connection.release();
  }
}



async function deleteSession(sessionId) {
  try {
    const sessionPath = `./auth_info_${sessionId}`;
    if (sessions[sessionId]) {
      const sock = sessions[sessionId].sock;

      // Fecha a conexão com o WhatsApp
      if (sock) {
        await sock.logout();
        console.log(`Conexão da sessão ${sessionId} encerrada.`);
      }

      // Remove do objeto de sessões
      delete sessions[sessionId];
      console.log(`Sessão ${sessionId} removida da memória.`);
    }

    // Remove a pasta de autenticação
    if (fs.existsSync(sessionPath)) {
      fs.rmSync(sessionPath, { recursive: true, force: true });
      console.log(`Pasta da sessão ${sessionId} apagada.`);
    }
  } catch (error) {
    console.error(`Erro ao remover a sessão ${sessionId}:`, error);
    throw error;
  }
}

// Adiciona endpoint para deletar sessão
app.delete('/end-session/:sessionId', async (req, res) => {
  const { sessionId } = req.params;

  if (!sessions[sessionId] && !fs.existsSync(`./auth_info_${sessionId}`)) {
    return res.status(404).json({ error: 'Sessão não encontrada.' });
  }

  try {
    await deleteSession(sessionId);
    res.json({ message: `Sessão ${sessionId} removida com sucesso.` });
  } catch (error) {
    res.status(500).json({ error: `Erro ao remover a sessão ${sessionId}: ${error.message}` });
  }
});


async function sendMessagesRoundRobin() {
  const activeSessions = getActiveSessions();

  if (activeSessions.length === 0) {
    console.log('Nenhuma sessão ativa para envio.');
    return;
  }

  const contacts = await fetchContactsToSend();

  for (const contact of contacts) {
    if (!isWorkingHours()) {
      console.log('Fora do horário de envio ou dia não útil. Pulando...');
      break; // Interrompe o envio se não estiver no horário ou for dia não útil
    }

    // Alterna entre as sessões ativas
    const sessionId = activeSessions[sessionIndex];
    const sock = sessions[sessionId].sock;

    await sendPersonalMessage(sock, contact); // Envia a mensagem utilizando a função adaptada

    // Avança para a próxima sessão no rodízio
    sessionIndex = (sessionIndex + 1) % activeSessions.length;
  }
}


const CHECK_INTERVAL = 10 * 60 * 1000; // Intervalo de 10 minutos em milissegundos

async function periodicMessageCheck() {
  while (true) {
    if (isWorkingHours()) {
      console.log('Dentro do horário de envio. Verificando novas mensagens...');
      try {
        await sendMessagesRoundRobin(); // Usa o rodízio de sessões
      } catch (error) {
        console.error('Erro durante o envio periódico de mensagens:', error);
      }
    } else {
      console.log('Fora do horário de envio. Aguardando...');
    }

    await delay(CHECK_INTERVAL);
  }
}




async function connectToWhatsApp(sessionId) {
  const sessionPath = `./auth_info_${sessionId}`;
  const { state, saveCreds } = await useMultiFileAuthState(sessionPath);

  const sock = makeWASocket({
    auth: state,
    printQRInTerminal: false,
    keepAliveIntervalMs: 60000,
  });

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      sessions[sessionId].qrCode = qr;
      console.log(`QR Code armazenado para a sessão ${sessionId}`);
    }

    if (connection === 'open') {
      console.log(`Sessão ${sessionId} conectada!`);
      sessions[sessionId].isConnected = true;

      
	  
	  
	  
	  
      // Inicia a verificação periódica de mensagens
      periodicMessageCheck(sock);
    } else if (connection === 'close') {
      console.log(`Conexão encerrada. Tentando reconectar...`);
      if (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut) {
        console.log('Reconectando devido a erro temporário...');
        await connectToWhatsApp(sessionId);
      } else {
        console.log('Conexão encerrada permanentemente. É necessário escanear o QR Code novamente.');
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);




  sessions[sessionId] = { sock, isConnected: false, qrCode: null };
  console.log(`Sessão ${sessionId} adicionada a 'sessions'`);
  return sock;
}

async function restoreSessions() {
  const sessionDirs = fs.readdirSync('.').filter(dir => dir.startsWith('auth_info_'));

  for (const dir of sessionDirs) {
    const sessionId = dir.split('auth_info_')[1];
    console.log(`Restaurando sessão: ${sessionId}`);
    await connectToWhatsApp(sessionId);
  }
}

app.post('/start-session/:sessionId', async (req, res) => {
  const { sessionId } = req.params;
  if (sessions[sessionId]) {
    return res.status(400).json({ error: 'Sessão já iniciada' });
  }
  await connectToWhatsApp(sessionId);
  res.json({ message: `Sessão ${sessionId} iniciada` });
});

app.get('/sessions', (req, res) => {
  const sessionList = Object.keys(sessions).map(sessionId => ({
    sessionId,
    isConnected: sessions[sessionId].isConnected,
  }));
  res.json(sessionList);
});

app.get('/qrcode/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  const session = sessions[sessionId];

  if (!session) {
    return res.status(404).send('Sessão não encontrada.');
  }

  if (session.qrCode) {
    res.setHeader('Content-Type', 'image/png');
    qrcode.toFileStream(res, session.qrCode);
  } else if (session.isConnected) {
    res.send('Sessão já está conectada.');
  } else {
    res.send('QR code não disponível no momento, tente novamente mais tarde.');
  }
});

app.listen(port, async () => {
  console.log(`Servidor rodando na porta ${port}`);
  await restoreSessions(); // Restaura sessões ao iniciar
});
