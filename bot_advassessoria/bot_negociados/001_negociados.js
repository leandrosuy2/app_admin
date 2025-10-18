const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const express = require('express');
const mysql = require('mysql2/promise');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const app = express();
app.use(express.json());
const port = 7001;

const sessions = {};
const sentConfirmations = new Map();

const dbConfig = {
  host: '127.0.0.1',
  user: 'advassessoria',
  password: 'Parceria@2025!',
  database: 'app',
  waitForConnections: true,
  connectionLimit: 100,
  queueLimit: 0,
};

const holidays = [
  '2024-01-01', '2024-02-12', '2024-02-13', '2024-03-29', '2024-04-21',
  '2024-05-01', '2024-05-30', '2024-09-07', '2024-10-12', '2024-11-02',
  '2024-11-15', '2024-12-25', '2025-01-01', '2025-02-17', '2025-02-18',
  '2025-04-18', '2025-04-21', '2025-05-01', '2025-06-19', '2025-09-07',
  '2025-10-12', '2025-11-02', '2025-11-15', '2025-12-25'
];

function isHoliday(date) {
  const formattedDate = date.toISOString().split('T')[0];
  return holidays.includes(formattedDate);
}

function isWorkingHours() {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const hour = now.getHours();
  const minute = now.getMinutes();

  if (dayOfWeek === 0 || dayOfWeek === 6 || isHoliday(now)) {
    console.log(`⏳ Fora do horário: Fim de semana ou feriado (${now.toISOString()})`);
    return false;
  }

  const currentTimeInMinutes = hour * 60 + minute;
  const startTimeInMinutes = 9 * 60; // 09:00
  const endTimeInMinutes = 19 * 60 + 59; // 17:59
  const isWithinHours = currentTimeInMinutes >= startTimeInMinutes && currentTimeInMinutes <= endTimeInMinutes;
  console.log(`🕒 Horário atual: ${hour}:${minute} - Dentro do horário? ${isWithinHours}`);
  return isWithinHours;
}

function getActiveSessions() {
  const active = Object.keys(sessions).filter(sessionId => sessions[sessionId].isConnected);
  console.log(`🔍 Sessões ativas: ${active.length} (${active.join(', ')})`);
  return active;
}

// Função para embaralhar array (Fisher-Yates shuffle)
function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

const pool = mysql.createPool(dbConfig);
app.use(express.static(path.join(__dirname, 'public')));

async function checkDatabaseConnection() {
  try {
    const connection = await pool.getConnection();
    console.log('✅ Conexão com o banco de dados estabelecida com sucesso');
    const [rows] = await connection.execute('SELECT 1 AS test');
    console.log(`🔍 Teste de query bem-sucedido: ${JSON.stringify(rows)}`);
    connection.release();
  } catch (error) {
    console.error(`❌ Erro ao conectar ao banco de dados: ${error.message}`);
  }
}

async function fetchContactsToSend(sessionId) {
  const connection = await pool.getConnection();
  try {
    console.log(`🔍 Buscando contatos para a sessão ${sessionId}`);
    const [contacts] = await connection.execute(`
      SELECT 
        d.id AS devedor_id,
        MAX(t.data_envio_whatsapp) AS ultima_data_envio_whatsapp,
        MAX(t.dataVencimento) AS ultima_dataVencimento,
        d.telefone,
        d.telefone1,
        d.telefone2,
        d.telefone3,
        d.telefone4,
        d.telefone5,
        d.telefone6,
        d.telefone7,
        d.telefone8,
        d.telefone9,
        d.telefone10,
        d.nome AS DevedorNome,
        d.nome_fantasia AS nome_fantasia_devedor,
        ce.nome_fantasia AS EmpresaNomeFantasia,
        MAX(t.statusBaixa) AS statusBaixa,
        MAX(t.data_baixa) AS ultima_data_baixa,
        ce.banco AS chavePix,
        SUM(t.valor) AS soma_valor_parcelas
      FROM devedores d
      JOIN core_empresa ce ON d.empresa_id = ce.id
      JOIN titulo t ON t.devedor_id = d.id
      WHERE
        t.statusBaixa = 3
        AND t.dataVencimento < CURDATE()
        AND (t.data_envio_whatsapp < CURDATE() OR t.data_envio_whatsapp IS NULL)
        AND t.data_baixa IS NULL
        AND ce.status_empresa = 1
        AND ce.operador = ?        
        AND (
          (d.telefone IS NOT NULL AND d.telefone <> '' AND (d.telefone_valido = "NAO VERIFICADO" OR d.telefone_valido = "SIM")) OR
          (d.telefone1 IS NOT NULL AND d.telefone1 <> '' AND (d.telefone1_valido = "NAO VERIFICADO" OR d.telefone1_valido = "SIM")) OR
          (d.telefone2 IS NOT NULL AND d.telefone2 <> '' AND (d.telefone2_valido = "NAO VERIFICADO" OR d.telefone2_valido = "SIM")) OR
          (d.telefone3 IS NOT NULL AND d.telefone3 <> '' AND (d.telefone3_valido = "NAO VERIFICADO" OR d.telefone3_valido = "SIM")) OR
          (d.telefone4 IS NOT NULL AND d.telefone4 <> '' AND (d.telefone4_valido = "NAO VERIFICADO" OR d.telefone4_valido = "SIM")) OR
          (d.telefone5 IS NOT NULL AND d.telefone5 <> '' AND (d.telefone5_valido = "NAO VERIFICADO" OR d.telefone5_valido = "SIM")) OR
          (d.telefone6 IS NOT NULL AND d.telefone6 <> '' AND (d.telefone6_valido = "NAO VERIFICADO" OR d.telefone6_valido = "SIM")) OR
          (d.telefone7 IS NOT NULL AND d.telefone7 <> '' AND (d.telefone7_valido = "NAO VERIFICADO" OR d.telefone7_valido = "SIM")) OR
          (d.telefone8 IS NOT NULL AND d.telefone8 <> '' AND (d.telefone8_valido = "NAO VERIFICADO" OR d.telefone8_valido = "SIM")) OR
          (d.telefone9 IS NOT NULL AND d.telefone9 <> '' AND (d.telefone9_valido = "NAO VERIFICADO" OR d.telefone9_valido = "SIM")) OR
          (d.telefone10 IS NOT NULL AND d.telefone10 <> '' AND (d.telefone10_valido = "NAO VERIFICADO" OR d.telefone10_valido = "SIM"))
        )
      GROUP BY d.id
      ORDER BY ultima_data_envio_whatsapp ASC;
    `, [sessionId]);

    console.log(`📋 Contatos encontrados para ${sessionId}: ${contacts.length}`);
    const contactMap = contacts.reduce((acc, contact) => {
      acc[contact.devedor_id] = {
        ...contact,
        telefones: [],
        sessionId: sessionId // Adiciona sessionId ao contato para referência posterior
      };
      const telefones = [
        contact.telefone, contact.telefone1, contact.telefone2, contact.telefone3,
        contact.telefone4, contact.telefone5, contact.telefone6, contact.telefone7,
        contact.telefone8, contact.telefone9, contact.telefone10
      ].filter(t => t && t !== '');

      for (const telefone of telefones) {
        let formattedPhone = telefone.replace(/\D/g, '');
        if (formattedPhone.length > 0) {
          let phone = formattedPhone.startsWith('55') ? formattedPhone : `55${formattedPhone}`;
          if (phone.length === 13) {
            const ddd = parseInt(phone.substring(2, 4), 10);
            if (ddd > 38) phone = phone.slice(0, 4) + phone.slice(5);
          }
          acc[contact.devedor_id].telefones.push(phone);
        }
      }
      return acc;
    }, {});
    const result = Object.values(contactMap);
    console.log(`📋 Contatos processados para ${sessionId}: ${result.length}`);
    return result;
  } catch (error) {
    console.error(`❌ Erro ao buscar contatos para ${sessionId}: ${error.message}`);
    return [];
  } finally {
    connection.release();
  }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function randomDelay() {
  const delays = [5000, 10000, 15000, 20000, 30000, 45000, 60000, 90000];
  const randomIndex = Math.floor(Math.random() * delays.length);
  const delayMs = delays[randomIndex];
  console.log(`⏲ Aguardando ${delayMs / 1000} segundos para a próxima mensagem...`);
  return delayMs;
}

async function sendPersonalMessage(sock, contact, sessionId) {
  if (!isWorkingHours()) {
    console.log('⏳ Fora do horário de envio. Pulando...');
    return;
  }

  const telefoneFields = [
    'telefone', 'telefone1', 'telefone2', 'telefone3', 'telefone4', 'telefone5',
    'telefone6', 'telefone7', 'telefone8', 'telefone9', 'telefone10'
  ];

  for (const telefone of contact.telefones) {
    const key = `${sessionId}:${telefone}`;
    if (sentConfirmations.has(key)) {
      console.log(`⏩ Mensagem já enviada para ${telefone} na sessão ${sessionId}. Pulando...`);
      continue;
    }

    console.log(`📌 Processando contato: ${contact.DevedorNome}, telefone: ${telefone}, sessão: ${sessionId}`);

    const confirmationMessage = `
🌟 *Olá, tudo bem?*  
Somos da *ADV Assessoria* e gostaríamos de falar com você.  
Por gentileza, estou falando com o(a) **${contact.DevedorNome}**?  
Por favor, responda com:  
✅ *1 - Sim*  
❌ *2 - Não*  
`;

    try {
      await sock.sendMessage(telefone + '@s.whatsapp.net', { text: confirmationMessage });
      console.log(`📨 Mensagem de confirmação enviada para ${telefone}`);
      await updateContactAsMessaged(contact.devedor_id);
      sentConfirmations.set(key, true);

      waitForResponse(sock, telefone).then(async (response) => {
        let validField;
        for (let i = 0; i < telefoneFields.length; i++) {
          const originalPhone = contact[telefoneFields[i]] ? contact[telefoneFields[i]].replace(/\D/g, '') : null;
          let formattedOriginal = originalPhone && (originalPhone.startsWith('55') ? originalPhone : `55${originalPhone}`);
          if (formattedOriginal && formattedOriginal.length === 13) {
            const ddd = parseInt(formattedOriginal.substring(2, 4), 10);
            if (ddd > 38) formattedOriginal = formattedOriginal.slice(0, 4) + formattedOriginal.slice(5);
          }
          if (formattedOriginal === telefone) {
            validField = telefoneFields[i] === 'telefone' ? 'telefone_valido' : `${telefoneFields[i]}_valido`;
            break;
          }
        }

        if (!validField) {
          console.error(`❌ Nenhum campo de telefone correspondente encontrado para ${telefone}`);
          return;
        }

        const isValid = response === '1' ? 'SIM' : 'NÃO';
        console.log(`📌 Atualizando ${validField} para ${isValid} para o devedor ID: ${contact.devedor_id}`);
        await updatePhoneValidity(contact.devedor_id, validField, isValid);
        
        // Atualiza data_envio_whatsapp após a resposta
        await updateContactAsMessaged(contact.devedor_id);
        console.log(`📅 Data de envio atualizada após resposta (${response}) para o devedor ID: ${contact.devedor_id}`);

        if (response === '1') {
          const overdueInstallments = await fetchOverdueInstallments(contact.devedor_id);
          const installmentsText = overdueInstallments.length > 0
            ? `⚠️ *Parcelas em atraso:*\n${overdueInstallments.map(i => `   - 💰 *Valor:* R$ ${i.valor.toFixed(2)} | 📅 *Vencimento:* ${formatDate(i.dataVencimento)}`).join('\n')}`
            : '⚠️ *Parcelas em atraso:*\n   - Nenhuma parcela encontrada.';

          const personalizedMessage = `
📢 *Prezado(a) ${contact.DevedorNome || 'Cliente'},*  
Meu nome é *Maria* e estou entrando em contato para lhe transmitir uma informação importante.  
🏢 *${contact.EmpresaNomeFantasia || 'Nossa Empresa'}* deseja auxiliá-lo(a) na regularização de sua pendência financeira.  
📜 *Detalhes da sua situação:*  
${installmentsText}  
💬 Você pode resolver essa questão de forma rápida e prática:  
📲 *Negocie agora mesmo pelo WhatsApp ou visite nossa loja:*  
📍 *${contact.EmpresaNomeFantasia || 'Nossa Empresa'}*  
Estamos à disposição para ajudar! Caso tenha dúvidas, não hesite em nos chamar.  
Atenciosamente,  
*Maria*  
📞 *Equipe de Atendimento*  
`;

          await sock.sendMessage(telefone + '@s.whatsapp.net', { text: personalizedMessage });
          console.log(`📨 Mensagem personalizada enviada para ${telefone}`);
        } else if (response === '2') {
          const apologyMessage = `
🙏 *Agradecemos por nos informar.*  
Registraremos sua solicitação e atualizaremos nosso banco de dados para que seu número não seja mais contatado.  
Caso tenha alguma dúvida ou precise de mais informações, estamos à disposição.  
Atenciosamente,  
📞 *Equipe de Atendimento*  
`;

          await sock.sendMessage(telefone + '@s.whatsapp.net', { text: apologyMessage });
          console.log(`📨 Mensagem de remoção enviada para ${telefone}`);
        }
      }).catch(error => {
        console.error(`❌ Erro ao aguardar resposta do contato ${telefone}: ${error}`);
      });
    } catch (error) {
      console.error(`❌ Erro ao enviar mensagem para ${telefone}: ${error.message}`);
    }

    await delay(randomDelay());
    return; // Processa um telefone por vez
  }
}

async function sendMessagesRoundRobin() {
  const activeSessions = getActiveSessions();
  if (activeSessions.length === 0) {
    console.log('❌ Nenhuma sessão ativa para envio.');
    return;
  }

  console.log(`🔄 Iniciando envio round-robin aleatório. Sessões ativas: ${activeSessions.length}`);
  
  // Coletar todos os contatos de todas as sessões em uma única lista
  let allContacts = [];
  for (const sessionId of activeSessions) {
    const contacts = await fetchContactsToSend(sessionId);
    allContacts = allContacts.concat(contacts);
  }

  // Embaralhar os contatos aleatoriamente
  allContacts = shuffleArray(allContacts);
  console.log(`📋 Total de contatos carregados e embaralhados: ${allContacts.length}`);

  // Processar os contatos um por um
  for (const contact of allContacts) {
    if (!isWorkingHours()) {
      console.log('⏳ Fora do horário de envio. Parando envio de mensagens.');
      break;
    }

    const sessionId = contact.sessionId; // Usa o sessionId associado ao contato
    const sock = sessions[sessionId].sock;
    console.log(`📨 Enviando mensagem para ${contact.DevedorNome} na sessão ${sessionId}`);
    await sendPersonalMessage(sock, contact, sessionId);
  }

  console.log('✅ Envio round-robin aleatório concluído ou fora do horário.');
}

async function waitForResponse(sock, telefone) {
  return new Promise((resolve) => {
    const messageHandler = (upsert) => {
      const messages = upsert.messages;
      for (const msg of messages) {
        const remoteJid = msg.key.remoteJid;
        const conversation = msg.message?.conversation?.trim().toLowerCase();

        if (remoteJid === telefone + '@s.whatsapp.net' && conversation) {
          console.log(`📩 Resposta recebida do número ${telefone}: ${conversation}`);
          const yesResponses = ['1', 'sim', 's', 'yes', 'y', 'si', 'sí'];
          const noResponses = ['2', 'não', 'nao', 'n', 'no'];

          if (yesResponses.includes(conversation)) {
            sock.ev.off('messages.upsert', messageHandler);
            resolve('1');
          } else if (noResponses.includes(conversation)) {
            sock.ev.off('messages.upsert', messageHandler);
            resolve('2');
          }
        }
      }
    };
    sock.ev.on('messages.upsert', messageHandler);
  });
}

async function updatePhoneValidity(devedorId, validField, isValid) {
  const connection = await pool.getConnection();
  try {
    const sql = `UPDATE devedores SET ${validField} = ? WHERE id = ?`;
    const [result] = await connection.execute(sql, [isValid, devedorId]);
    console.log(result.affectedRows > 0
      ? `✅ Campo ${validField} atualizado para ${isValid} (ID: ${devedorId})`
      : `⚠️ Nenhuma linha atualizada para o ID: ${devedorId}`);
  } catch (error) {
    console.error(`❌ Erro ao atualizar ${validField}: ${error.message}`);
  } finally {
    connection.release();
  }
}

function formatDate(date) {
  const d = new Date(date);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
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
    return installments;
  } catch (error) {
    console.error(`❌ Erro ao buscar parcelas vencidas para ID ${devedorId}: ${error.message}`);
    return [];
  } finally {
    connection.release();
  }
}

async function updateContactAsMessaged(devedorId) {
  const connection = await pool.getConnection();
  try {
    const now = new Date().toISOString().split('T')[0];
    const sql = "UPDATE titulo SET data_envio_whatsapp = ? WHERE devedor_id = ?";
    const [result] = await connection.execute(sql, [now, devedorId]);
    console.log(result.affectedRows > 0 
      ? `✅ Data de envio atualizada (ID: ${devedorId})`
      : `⚠️ Nenhuma linha atualizada para o ID: ${devedorId}`);
  } catch (error) {
    console.error(`❌ Erro ao atualizar data_envio_whatsapp: ${error.message}`);
  } finally {
    connection.release();
  }
}

async function deleteSession(sessionId) {
  try {
    const sessionPath = `./auth_info_${sessionId}`;
    
    // Verifica se a sessão está ativa na memória e tenta desconectá-la
    if (sessions[sessionId]) {
      const sock = sessions[sessionId].sock;
      if (sock) {
        try {
          await sock.logout(); // Tenta desconectar, mas ignora erros específicos
          console.log(`🔌 Sessão ${sessionId} desconectada com sucesso`);
        } catch (logoutError) {
          console.warn(`⚠️ Falha ao desconectar sessão ${sessionId} (provavelmente já fechada): ${logoutError.message}`);
        }
      } else {
        console.log(`⚠️ Socket não encontrado para a sessão ${sessionId}`);
      }
      delete sessions[sessionId]; // Remove da memória independentemente do logout
      console.log(`🗑 Sessão ${sessionId} removida da memória`);
    } else {
      console.log(`⚠️ Sessão ${sessionId} não encontrada na memória`);
    }

    // Remove a pasta da sessão, se existir
    if (fs.existsSync(sessionPath)) {
      await fs.promises.rm(sessionPath, { recursive: true, force: true });
      console.log(`✅ Pasta da sessão ${sessionId} apagada: ${sessionPath}`);
    } else {
      console.log(`⚠️ Pasta da sessão ${sessionId} não encontrada: ${sessionPath}`);
    }
  } catch (error) {
    console.error(`❌ Erro ao remover sessão ${sessionId}: ${error.message}`);
    throw error; // Propaga o erro para o endpoint
  }
}

// Endpoint DELETE ajustado
app.delete('/end-session/:sessionId', async (req, res) => {
  const { sessionId } = req.params;
  
  // Verifica se a sessão existe na memória ou no sistema de arquivos
  if (!sessions[sessionId] && !fs.existsSync(`./auth_info_${sessionId}`)) {
    return res.status(404).json({ error: 'Sessão não encontrada' });
  }

  try {
    await deleteSession(sessionId);
    res.json({ message: `Sessão ${sessionId} removida com sucesso` });
  } catch (error) {
    res.status(500).json({ error: `Erro ao remover sessão ${sessionId}: ${error.message}` });
  }
});

const CHECK_INTERVAL = 10 * 60 * 1000; // 10 minutos

async function periodicMessageCheck() {
  while (true) {
    if (isWorkingHours()) {
      console.log('✅ Dentro do horário de envio. Verificando novas mensagens...');
      try {
        await sendMessagesRoundRobin();
      } catch (error) {
        console.error(`❌ Erro durante o envio periódico de mensagens: ${error.message}`);
      }
    } else {
      console.log('⏳ Fora do horário de envio. Aguardando...');
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

  sessions[sessionId] = { sock, isConnected: false, qrCode: null };

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      sessions[sessionId].qrCode = qr;
      console.log(`📌 QR Code gerado para ${sessionId}`);
    }
    if (connection === 'open') {
      sessions[sessionId].isConnected = true;
      sessions[sessionId].qrCode = null;
      console.log(`✅ Sessão ${sessionId} conectada com sucesso`);
      setTimeout(async () => {
        if (isWorkingHours()) {
          console.log(`📨 Iniciando envio automático para a sessão ${sessionId}`);
          await sendMessagesRoundRobin();
        } else {
          console.log(`⏳ Sessão ${sessionId} conectada, mas fora do horário de envio`);
        }
      }, 5000);
    } else if (connection === 'close') {
      sessions[sessionId].isConnected = false;
      console.log(`🔴 Sessão ${sessionId} desconectada`);
      if (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut) {
        console.log('🔄 Tentando reconectar...');
        await connectToWhatsApp(sessionId);
      } else {
        console.log('❌ Sessão desconectada permanentemente.');
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);
  return sock;
}

async function restoreSessions() {
  const sessionDirs = fs.readdirSync('.').filter(dir => dir.startsWith('auth_info_'));
  console.log(`🔍 Restaurando ${sessionDirs.length} sessões salvas`);
  for (const dir of sessionDirs) {
    const sessionId = dir.split('auth_info_')[1];
    console.log(`Restaurando sessão: ${sessionId}`);
    await connectToWhatsApp(sessionId);
  }
}

app.post('/start-session/:sessionId', async (req, res) => {
  const { sessionId } = req.params;
  if (sessions[sessionId]) return res.status(400).json({ error: 'Sessão já iniciada' });
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
  if (!session) return res.status(404).send('Sessão não encontrada.');
  if (session.qrCode) {
    res.setHeader('Content-Type', 'image/png');
    qrcode.toFileStream(res, session.qrCode);
  } else if (session.isConnected) {
    res.send('Sessão já conectada.');
  } else {
    res.send('QR code não disponível.');
  }
});

app.listen(port, async () => {
  console.log(`🚀 Servidor rodando na porta ${port}`);
  await checkDatabaseConnection();
  await restoreSessions();
  periodicMessageCheck();
});
