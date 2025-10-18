const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const express = require('express');
const mysql = require('mysql2/promise');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const app = express();
app.use(express.json());
const port = 7002;

const sessions = {};

const dbConfig = {
  host: '127.0.0.1',
  user: 'advassessoria',
  password: 'Parceria@2025!',
  database: 'app',
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
  const endTimeInMinutes = 19 * 60 + 59; // 17:59

  return currentTimeInMinutes >= startTimeInMinutes && currentTimeInMinutes <= endTimeInMinutes;
}


function getActiveSessions() {
  return Object.keys(sessions).filter(sessionId => sessions[sessionId].isConnected);
}


const pool = mysql.createPool(dbConfig);

app.use(express.static(path.join(__dirname, 'public')));

async function fetchContactsToSend(sessionId) {
  const connection = await pool.getConnection();
  try {
    const [contacts] = await connection.execute(`
      SELECT 
    MAX(devedores.id) AS devedor_id,
    MAX(titulo.data_envio_whatsapp) AS ultima_data_envio_whatsapp,
    MAX(titulo.dataVencimento) AS ultima_dataVencimento,
    t.telefone,
    MAX(devedores.nome) AS DevedorNome,
    MAX(devedores.nome_fantasia) AS nome_fantasia_devedor,
    MAX(core_empresa.nome_fantasia) AS EmpresaNomeFantasia,
    MAX(titulo.statusBaixa) AS statusBaixa,
    MAX(titulo.data_baixa) AS ultima_data_baixa,
    MAX(core_empresa.nome_fantasia) AS nome_fantasia_empresa,
    MAX(core_empresa.banco) AS chavePix,
    SUM(titulo.valor) AS soma_valor_parcelas
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
    (titulo.statusBaixa = 0 or titulo.statusBaixa is null)
    AND titulo.dataVencimento < CURDATE()
    AND (titulo.data_envio_whatsapp < CURDATE() OR titulo.data_envio_whatsapp IS NULL)
    AND t.telefone IS NOT NULL
    AND t.telefone <> ''     
    AND titulo.data_baixa IS NULL
    AND core_empresa.status_empresa = 1
    AND core_empresa.operador = ?
    AND (devedores.telefone_valido = "NAO VERIFICADO" OR devedores.telefone_valido = "SIM")
GROUP BY t.telefone
ORDER BY ultima_data_envio_whatsapp ASC;
    `, [sessionId]);  // <- Filtro baseado no operador (sessionId)

    const contactMap = contacts.reduce((acc, contact) => {
      let formattedPhone = contact.telefone.replace(/\D/g, ''); // Remove caracteres não numéricos

      if (formattedPhone.length > 0) {
        if (!acc[contact.devedor_id]) {
          acc[contact.devedor_id] = {
            ...contact,
            telefones: [],
          };
        }

        // Adiciona "55" se não estiver presente
        let phone = formattedPhone.startsWith('55') ? formattedPhone : `55${formattedPhone}`;

        // **Nova lógica para remover o quinto dígito apenas se o DDD for maior que 38**
        if (phone.length === 13) { // Exemplo: 5511998765432
          const ddd = parseInt(phone.substring(2, 4), 10); // Extrai o DDD
          if (ddd > 38) {
            phone = phone.slice(0, 4) + phone.slice(5); // Remove o quinto dígito
          }
        }

        acc[contact.devedor_id].telefones.push(phone);
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
// Função para enviar mensagens personalizadas e processar respostas
async function sendPersonalMessage(sock, contact) {
    if (!isWorkingHours()) {
        console.log('Fora do horário de envio ou dia não útil. Pulando...');
        return;
    }

    for (const [index, telefone] of contact.telefones.entries()) {
        if (sentConfirmations.has(telefone)) {
            console.log(`Mensagem já enviada para ${telefone}. Pulando...`);
            continue;
        }

        console.log(`📌 Processando contato: ${contact.DevedorNome}, telefone: ${telefone}`);

        const devedorId = contact.devedor_id || contact.id;

        if (!devedorId) {
            console.error(`❌ ERRO: devedor_id está indefinido para o telefone ${telefone}`);
            continue;
        }

        // Mensagem de confirmação
        const confirmationMessage = `
🌟 *Olá, tudo bem?*  

Somos da *ADV Assessoria* e gostaríamos de falar com você.  

Por gentileza, estou falando com o(a) **${contact.DevedorNome}**?  

Por favor, responda com:  

✅ *1 - Sim*  
❌ *2 - Não*  
`;


        await sock.sendMessage(telefone + '@s.whatsapp.net', { text: confirmationMessage });
        console.log(`📨 Mensagem de confirmação enviada para ${telefone}`);

        // Atualiza no banco que a mensagem foi enviada
        await updateContactAsMessaged(devedorId);

        sentConfirmations.add(telefone);

        // Aguarda resposta em segundo plano
        waitForResponse(sock, telefone).then(async (response) => {
            const validField = `telefone${index + 1}_valido`;
            const isValid = response === '1' ? "SIM" : "NÃO";

            console.log(`📌 Atualizando ${validField} para ${isValid} no banco de dados para o devedor ID: ${devedorId}`);
            await updatePhoneValidity(devedorId, validField, isValid);

            if (response === '1') {
                const overdueInstallments = await fetchOverdueInstallments(devedorId);
                const installmentsText = overdueInstallments.length > 0
                    ? `⚠️ *Parcelas em atraso:*\n${overdueInstallments.map(installment => {
                        return `   - 💰 *Valor:* R$ ${installment.valor.toFixed(2)} | 📅 *Vencimento:* ${formatDate(installment.dataVencimento)}`;
                    }).join('\n')}`
                    : '⚠️ *Parcelas em atraso:*\n   - Nenhuma parcela encontrada.';

                const personalizedMessage = `
📢 *Olá, ${contact.DevedorNome || 'Cliente'}!*  

Somos da *ADV Assessoria & Associados* e estamos entrando em contato referente a uma pendência registrada em nome da empresa *${contact.EmpresaNomeFantasia || 'Nossa Empresa'}*.  

Estamos oferecendo condições especiais para quitação, incluindo:  
✅ *Parcelamento facilitado*  
✅ *Descontos em juros*  
✅ *Descontos incríveis para pagamento à vista*  

💬 *Não perca essa oportunidade de resolver sua pendência de forma simples e rápida.*  

📞 *Fale conosco pelo WhatsApp para mais informações e suporte.*  
🏢 *Ou visite a loja ${contact.EmpresaNomeFantasia || 'Nossa Empresa'} para negociar diretamente.*  

📌 *Escritório Jurídico*  
*ADV Assessoria & Associados*  
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
            console.error(`Erro ao aguardar resposta do contato ${telefone}: ${error}`);
        });

        // **Segue para o próximo contato imediatamente sem esperar a resposta**
        await delay(randomDelay());
    }
}







async function sendMessagesRoundRobin() {
  const activeSessions = getActiveSessions();

  if (activeSessions.length === 0) {
    console.log('❌ Nenhuma sessão ativa para envio.');
    return;
  }

  console.log(`🔄 Iniciando o envio de mensagens. Sessões ativas: ${activeSessions.length}`);

  for (const sessionId of activeSessions) {
    if (!isWorkingHours()) {
      console.log('⏳ Fora do horário de envio ou dia não útil. Pulando...');
      break;
    }

    console.log(`📌 Buscando contatos para a sessão ${sessionId}...`);
    const contacts = await fetchContactsToSend(sessionId);

    if (contacts.length === 0) {
      console.log(`⚠️ Nenhum contato encontrado para envio na sessão ${sessionId}.`);
      continue;
    }

    const sock = sessions[sessionId].sock;

    for (const contact of contacts) {
      if (!isWorkingHours()) {
        console.log('⏳ Fora do horário de envio. Parando envio de mensagens.');
        break;
      }

      console.log(`📨 Enviando mensagem para ${contact.DevedorNome}, telefone(s): ${contact.telefones.join(', ')}`);
      await sendPersonalMessage(sock, contact);

      // Aguarda um tempo antes de processar o próximo contato
      await delay(randomDelay());
    }
  }
}



// Função para aguardar a resposta do usuário
async function waitForResponse(sock, telefone) {
    return new Promise((resolve) => {
        const messageHandler = (upsert) => {
            const messages = upsert.messages;
            for (const msg of messages) {
                const remoteJid = msg.key.remoteJid;
                const conversation = msg.message?.conversation?.trim().toLowerCase();

                if (remoteJid === telefone + '@s.whatsapp.net' && conversation) {
                    console.log(`Resposta recebida do número ${telefone}: ${conversation}`);

                    const yesResponses = ['1', 'sim', 's', 'yes', 'y', 'si', 'sí'];
                    const noResponses = ['2', 'não', 'nao', 'n', 'no'];

                    if (yesResponses.includes(conversation)) {
                        sock.ev.off('messages.upsert', messageHandler);
                        resolve('1'); // Respondeu "Sim"
                    } else if (noResponses.includes(conversation)) {
                        sock.ev.off('messages.upsert', messageHandler);
                        resolve('2'); // Respondeu "Não"
                    }
                }
            }
        };

        sock.ev.on('messages.upsert', messageHandler);
    });
}


async function updatePhoneValidity(devedorId, validField, isValid) {
    if (!devedorId || !validField) {
        console.error(`❌ ERRO: Tentativa de atualizar ${validField} com um devedor_id inválido.`);
        return;
    }

    const connection = await pool.getConnection();
    try {
        const sql = `UPDATE devedores SET ${validField} = ? WHERE id = ?`;
        const [result] = await connection.execute(sql, [isValid, devedorId]);

        if (result.affectedRows === 0) {
            console.log(`⚠️ Nenhuma linha atualizada para o devedor ID: ${devedorId}.`);
        } else {
            console.log(`✅ Campo ${validField} atualizado para ${isValid} para o devedor ID: ${devedorId}.`);
        }
    } catch (error) {
        console.error(`❌ ERRO ao atualizar o campo de validade do telefone: ${error.message}`);
    } finally {
        connection.release();
    }
}



// Função para remover contato do banco de dados
/*
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
*/

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




async function updateContactAsMessaged(devedorId) {
    if (!devedorId) {
        console.error("❌ ERRO: Tentativa de atualizar `data_envio_whatsapp` com um devedor_id indefinido.");
        return;
    }

    const connection = await pool.getConnection();
    try {
        const now = new Date();
        const formattedDate = now.toISOString().split('T')[0];

        const sql = "UPDATE titulo SET data_envio_whatsapp = ? WHERE devedor_id = ?";
        const [result] = await connection.execute(sql, [formattedDate, devedorId]);

        if (result.affectedRows === 0) {
            console.log(`⚠️ Nenhuma linha atualizada para o devedor ID: ${devedorId}. Verifique se o ID existe.`);
        } else {
            console.log(`✅ Data de envio WhatsApp atualizada para o devedor ID: ${devedorId}.`);
        }
    } catch (error) {
        console.error(`❌ ERRO ao atualizar data_envio_whatsapp para o devedor ID ${devedorId}:`, error);
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
    printQRInTerminal: false, // Garante que o QR Code não seja impresso no terminal
    keepAliveIntervalMs: 60000,
  });

  sessions[sessionId] = { sock, isConnected: false, qrCode: null };

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      sessions[sessionId].qrCode = qr;
      console.log(`📌 QR Code gerado para a sessão ${sessionId}`);
    }

    if (connection === 'open') {
      console.log(`✅ Sessão ${sessionId} conectada com sucesso!`);
      sessions[sessionId].isConnected = true;
      sessions[sessionId].qrCode = null; // Remove o QR Code após conexão

      // Aguarda 5 segundos e inicia o envio automático
      setTimeout(async () => {
        if (isWorkingHours()) {
          console.log(`📨 Iniciando envio automático para a sessão ${sessionId}`);
          await sendMessagesRoundRobin();  // Chama a função de envio após conectar
        }
      }, 5000);

    } else if (connection === 'close') {
      console.log(`🔴 Sessão ${sessionId} desconectada.`);
      sessions[sessionId].isConnected = false;

      if (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut) {
        console.log('Tentando reconectar...');
        await connectToWhatsApp(sessionId);
      } else {
        console.log('Sessão desconectada permanentemente. Será necessário escanear o QR Code novamente.');
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);
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
