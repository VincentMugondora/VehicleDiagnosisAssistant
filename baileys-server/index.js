const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys')
const express = require('express')
const axios = require('axios')

const app = express()
app.use(express.json())

let sock = null

// Configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/webhook/baileys'
const API_KEY = process.env.BAILEYS_API_KEY || 'your-secret-key-here'
const PORT = process.env.PORT || 3000

async function connectToWhatsApp() {
    console.log('🔄 Connecting to WhatsApp...')

    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')

    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        browser: ['Vehicle Diagnosis Assistant', 'Chrome', '1.0.0']
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update

        if (qr) {
            console.log('📱 Scan this QR code with WhatsApp:')
        }

        if(connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut
            console.log('❌ Connection closed. Reconnecting:', shouldReconnect)

            if(shouldReconnect) {
                setTimeout(() => connectToWhatsApp(), 3000)
            } else {
                console.log('🚪 Logged out. Delete auth_info_baileys folder to reconnect.')
            }
        } else if(connection === 'open') {
            console.log('✅ WhatsApp Connected!')
            console.log('📱 Ready to receive messages')
        }
    })

    // Handle incoming messages
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return

        const msg = messages[0]
        if (!msg.message || msg.key.fromMe) return

        const from = msg.key.remoteJid
        const text = msg.message.conversation ||
                     msg.message.extendedTextMessage?.text ||
                     msg.message.imageMessage?.caption || ''

        const messageId = msg.key.id

        console.log(`\n📩 Message from ${from}`)
        console.log(`   Text: ${text}`)

        try {
            // Send typing indicator
            await sock.sendPresenceUpdate('composing', from)

            // Send to your FastAPI backend
            const response = await axios.post(BACKEND_URL, {
                from: from,
                sender: from,
                text: text,
                message: text,
                message_id: messageId
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                timeout: 30000 // 30 second timeout
            })

            // Stop typing indicator
            await sock.sendPresenceUpdate('paused', from)

            // Send reply back to WhatsApp
            const reply = response.data.reply

            // Split long messages (WhatsApp limit ~4096 chars)
            const chunks = splitMessage(reply, 4000)

            for (const chunk of chunks) {
                await sock.sendMessage(from, { text: chunk })
                // Small delay between chunks
                if (chunks.length > 1) {
                    await sleep(500)
                }
            }

            console.log(`✅ Sent reply (${chunks.length} message${chunks.length > 1 ? 's' : ''})`)

        } catch (error) {
            console.error('❌ Error:', error.message)

            // Send error message to user
            await sock.sendMessage(from, {
                text: 'Sorry, there was an error processing your request. Please try again later.'
            })
        }
    })
}

// Helper function to split long messages
function splitMessage(text, maxLength) {
    if (text.length <= maxLength) return [text]

    const chunks = []
    let currentChunk = ''

    const lines = text.split('\n')

    for (const line of lines) {
        if ((currentChunk + line + '\n').length > maxLength) {
            if (currentChunk) chunks.push(currentChunk.trim())
            currentChunk = line + '\n'
        } else {
            currentChunk += line + '\n'
        }
    }

    if (currentChunk) chunks.push(currentChunk.trim())

    return chunks
}

// Helper function for delays
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

// API endpoint to send messages manually (optional)
app.post('/send', async (req, res) => {
    const { to, message } = req.body

    if (!sock) {
        return res.status(503).json({ error: 'WhatsApp not connected' })
    }

    try {
        // Ensure number has @s.whatsapp.net suffix
        const formattedTo = to.includes('@') ? to : `${to}@s.whatsapp.net`
        await sock.sendMessage(formattedTo, { text: message })
        res.json({ success: true, message: 'Message sent' })
    } catch (error) {
        res.status(500).json({ error: error.message })
    }
})

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        connected: sock !== null,
        backend: BACKEND_URL
    })
})

// Start server
app.listen(PORT, () => {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('🚀 Baileys WhatsApp Server')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log(`📡 Server running on port ${PORT}`)
    console.log(`🔗 Backend URL: ${BACKEND_URL}`)
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    connectToWhatsApp()
})

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n👋 Shutting down gracefully...')
    if (sock) {
        await sock.logout()
    }
    process.exit(0)
})
