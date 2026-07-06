require('dotenv').config()
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys')
const qrcode = require('qrcode-terminal')
const express = require('express')
const axios = require('axios')
const helmet = require('helmet')
const rateLimit = require('express-rate-limit')
const { body, validationResult } = require('express-validator')
const { v4: uuidv4 } = require('uuid')
const pino = require('pino')

const app = express()
let sock = null
let server = null

// Metrics tracking
const metrics = {
    startTime: Date.now(),
    messagesReceived: 0,
    messagesSent: 0,
    errors: 0,
    lastMessageTime: null,
    connectionStatus: 'disconnected',
    reconnectAttempts: 0
}

// Logger setup
const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    transport: process.env.NODE_ENV !== 'production' ? {
        target: 'pino-pretty',
        options: {
            colorize: true,
            translateTime: 'SYS:standard',
            ignore: 'pid,hostname'
        }
    } : undefined
})

// Environment validation
function validateEnvironment() {
    const required = {
        BACKEND_URL: process.env.BACKEND_URL,
        BAILEYS_API_KEY: process.env.BAILEYS_API_KEY
    }

    const missing = []
    const weak = []

    for (const [key, value] of Object.entries(required)) {
        if (!value) {
            missing.push(key)
        } else if (key === 'BAILEYS_API_KEY' && value.length < 32) {
            weak.push(`${key} (minimum 32 characters required, got ${value.length})`)
        } else if (key === 'BAILEYS_API_KEY' && /^(your-secret-key|changeme|password|test)/i.test(value)) {
            weak.push(`${key} (using weak/default value)`)
        }
    }

    if (missing.length > 0) {
        logger.error({ missing }, 'Missing required environment variables')
        throw new Error(`Missing required environment variables: ${missing.join(', ')}. Copy .env.example to .env and configure.`)
    }

    if (weak.length > 0) {
        logger.error({ weak }, 'Weak environment variable values detected')
        throw new Error(`Weak environment variable values: ${weak.join(', ')}. Use strong, random keys in production.`)
    }

    // Validate BACKEND_URL format (SSRF protection)
    try {
        const url = new URL(process.env.BACKEND_URL)
        if (!['http:', 'https:'].includes(url.protocol)) {
            throw new Error('BACKEND_URL must use http:// or https://')
        }
        // Prevent localhost/internal IPs in production
        if (process.env.NODE_ENV === 'production') {
            const hostname = url.hostname.toLowerCase()
            if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') ||
                hostname.startsWith('10.') || hostname.startsWith('172.')) {
                logger.warn('BACKEND_URL uses internal IP in production - ensure this is intentional')
            }
        }
    } catch (error) {
        throw new Error(`Invalid BACKEND_URL format: ${error.message}`)
    }

    logger.info('Environment validation passed')
}

// Configuration
const CONFIG = {
    BACKEND_URL: process.env.BACKEND_URL,
    API_KEY: process.env.BAILEYS_API_KEY,
    PORT: parseInt(process.env.PORT || '3000', 10),
    REQUEST_TIMEOUT: parseInt(process.env.REQUEST_TIMEOUT || '60000', 10),
    RATE_LIMIT_MAX: parseInt(process.env.RATE_LIMIT_MAX || '20', 10),
    RATE_LIMIT_WINDOW: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10),
    ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS?.split(',').map(s => s.trim()) || []
}

// Request ID middleware
app.use((req, res, next) => {
    req.id = uuidv4()
    res.setHeader('X-Request-ID', req.id)
    logger.info({ requestId: req.id, method: req.method, url: req.url, ip: req.ip }, 'Incoming request')
    next()
})

// Security headers
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"]
        }
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
}))

// CORS configuration
const corsOptions = {
    origin: (origin, callback) => {
        if (!origin || CONFIG.ALLOWED_ORIGINS.length === 0 || CONFIG.ALLOWED_ORIGINS.includes(origin)) {
            callback(null, true)
        } else {
            callback(new Error('Not allowed by CORS'))
        }
    },
    credentials: true,
    optionsSuccessStatus: 200
}

if (CONFIG.ALLOWED_ORIGINS.length > 0) {
    const cors = require('cors')
    app.use(cors(corsOptions))
    logger.info({ origins: CONFIG.ALLOWED_ORIGINS }, 'CORS enabled')
}

// Request size limits
app.use(express.json({ limit: '100kb' }))
app.use(express.urlencoded({ extended: true, limit: '100kb' }))

// Serve cached diagram images (static files, no auth required for WhatsApp access)
app.use('/cached-images', express.static('cached-images', {
    maxAge: '1y',  // Cache for 1 year
    immutable: true
}))

// Rate limiting
const limiter = rateLimit({
    windowMs: CONFIG.RATE_LIMIT_WINDOW,
    max: CONFIG.RATE_LIMIT_MAX,
    message: { error: 'Too many requests, please try again later.' },
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
        logger.warn({ requestId: req.id, ip: req.ip }, 'Rate limit exceeded')
        res.status(429).json({ error: 'Too many requests, please try again later.' })
    }
})

app.use('/send', limiter)

// Authentication middleware
function authenticateApiKey(req, res, next) {
    const apiKey = req.headers['x-api-key']

    if (!apiKey) {
        logger.warn({ requestId: req.id, ip: req.ip }, 'Missing API key')
        return res.status(401).json({ error: 'Authentication required' })
    }

    if (apiKey !== CONFIG.API_KEY) {
        logger.warn({ requestId: req.id, ip: req.ip }, 'Invalid API key')
        return res.status(403).json({ error: 'Invalid API key' })
    }

    next()
}

// Input validation middleware
const validateSendMessage = [
    body('to')
        .trim()
        .notEmpty().withMessage('Recipient phone number is required')
        .matches(/^[\d+\-\s()]+$/).withMessage('Invalid phone number format')
        .customSanitizer(value => value.replace(/[\s\-()]/g, '')),
    body('message')
        .trim()
        .notEmpty().withMessage('Message is required')
        .isLength({ max: 4096 }).withMessage('Message too long (max 4096 characters)'),
    (req, res, next) => {
        const errors = validationResult(req)
        if (!errors.isEmpty()) {
            logger.warn({ requestId: req.id, errors: errors.array() }, 'Validation failed')
            return res.status(400).json({ error: 'Validation failed', details: errors.array() })
        }
        next()
    }
]

// Exponential backoff for reconnection
let reconnectAttempt = 0
const RECONNECT_DELAYS = [3000, 6000, 12000, 30000, 60000]

function getReconnectDelay() {
    const delay = RECONNECT_DELAYS[Math.min(reconnectAttempt, RECONNECT_DELAYS.length - 1)]
    reconnectAttempt++
    return delay
}

function resetReconnectAttempt() {
    reconnectAttempt = 0
}

// Improved message splitting
function splitMessage(text, maxLength = 4000) {
    if (!text || text.length <= maxLength) return [text || '']

    const chunks = []
    const paragraphs = text.split('\n\n')
    let currentChunk = ''

    for (const paragraph of paragraphs) {
        if (!paragraph) continue

        if ((currentChunk + '\n\n' + paragraph).length > maxLength) {
            if (currentChunk) {
                chunks.push(currentChunk.trim())
                currentChunk = ''
            }

            if (paragraph.length > maxLength) {
                const words = paragraph.split(' ')
                for (const word of words) {
                    if ((currentChunk + ' ' + word).length > maxLength) {
                        if (currentChunk) chunks.push(currentChunk.trim())
                        currentChunk = word
                    } else {
                        currentChunk += (currentChunk ? ' ' : '') + word
                    }
                }
            } else {
                currentChunk = paragraph
            }
        } else {
            currentChunk += (currentChunk ? '\n\n' : '') + paragraph
        }
    }

    if (currentChunk) chunks.push(currentChunk.trim())

    return chunks.length > 0 ? chunks : [text.substring(0, maxLength)]
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

// WhatsApp connection
async function connectToWhatsApp() {
    logger.info('Connecting to WhatsApp...')
    metrics.connectionStatus = 'connecting'

    try {
        const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')

        sock = makeWASocket({
            auth: state,
            printQRInTerminal: true,
            browser: ['Vehicle Diagnosis Assistant', 'Chrome', '1.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 30000,
            logger: pino({ level: 'silent' }),
            markOnlineOnConnect: true
        })

        sock.ev.on('creds.update', saveCreds)

        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update

            if (qr) {
                logger.info('QR code received - displaying in terminal')
                console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                console.log('📱 SCAN THIS QR CODE WITH WHATSAPP')
                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

                // Generate QR code in terminal (printQRInTerminal also does this, but double display for visibility)
                try {
                    qrcode.generate(qr, { small: true })
                } catch (qrError) {
                    logger.error({ error: qrError.message }, 'Failed to generate QR code')
                    console.log('QR Code Data:', qr)
                }

                console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                console.log('📱 Open WhatsApp → Settings → Linked Devices')
                console.log('📲 Tap "Link a Device" and scan the code above')
                console.log('⏱️  QR code refreshes every 60 seconds')
                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
            }

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut

                metrics.connectionStatus = 'disconnected'
                metrics.reconnectAttempts++

                logger.warn({
                    statusCode,
                    shouldReconnect,
                    attempt: reconnectAttempt
                }, 'Connection closed')

                if (shouldReconnect) {
                    const delay = getReconnectDelay()
                    logger.info({ delay }, `Reconnecting in ${delay}ms...`)
                    setTimeout(() => connectToWhatsApp(), delay)
                } else {
                    logger.error('Logged out. Delete auth_info_baileys folder to reconnect.')
                    metrics.connectionStatus = 'logged_out'
                }
            } else if (connection === 'open') {
                logger.info('WhatsApp connected successfully')
                metrics.connectionStatus = 'connected'
                resetReconnectAttempt()
                console.log('✅ WhatsApp Connected!')
                console.log('📱 Ready to receive messages')
            }
        })

        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type !== 'notify') return

            const msg = messages[0]
            if (!msg.message || msg.key.fromMe) return

            const from = msg.key.remoteJid

            if (from === 'status@broadcast' || from.endsWith('@g.us')) {
                logger.debug({ from }, 'Skipping broadcast/group message')
                return
            }

            const text = msg.message.conversation ||
                         msg.message.extendedTextMessage?.text ||
                         msg.message.imageMessage?.caption || ''

            const messageId = msg.key.id
            const requestId = uuidv4()

            metrics.messagesReceived++
            metrics.lastMessageTime = Date.now()

            logger.info({
                requestId,
                from,
                messageId,
                textLength: text.length
            }, 'Message received')

            try {
                await sock.sendPresenceUpdate('composing', from)

                const response = await axios.post(CONFIG.BACKEND_URL, {
                    from,
                    sender: from,
                    text,
                    message: text,
                    message_id: messageId,
                    request_id: requestId
                }, {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': CONFIG.API_KEY,
                        'X-Request-ID': requestId
                    },
                    timeout: CONFIG.REQUEST_TIMEOUT,
                    validateStatus: (status) => status < 500
                })

                await sock.sendPresenceUpdate('paused', from)

                if (response.status >= 400) {
                    throw new Error(`Backend returned ${response.status}: ${JSON.stringify(response.data)}`)
                }

                const reply = response.data.reply || 'No response from backend'
                const chunks = splitMessage(reply, 4000)

                for (const chunk of chunks) {
                    await sock.sendMessage(from, { text: chunk })
                    metrics.messagesSent++
                    if (chunks.length > 1) {
                        await sleep(500)
                    }
                }

                logger.info({
                    requestId,
                    from,
                    chunks: chunks.length
                }, 'Reply sent successfully')

            } catch (error) {
                metrics.errors++
                logger.error({
                    requestId,
                    from,
                    error: error.message,
                    code: error.code,
                    backendUrl: CONFIG.BACKEND_URL,
                    stack: error.stack
                }, 'Error processing message')

                try {
                    await sock.sendMessage(from, {
                        text: 'Sorry, there was an error processing your request. Please try again later.'
                    })
                } catch (sendError) {
                    logger.error({ requestId, error: sendError.message }, 'Failed to send error message')
                }
            }
        })

    } catch (error) {
        metrics.errors++
        logger.error({ error: error.message, stack: error.stack }, 'Failed to connect to WhatsApp')

        const delay = getReconnectDelay()
        logger.info({ delay }, `Retrying connection in ${delay}ms...`)
        setTimeout(() => connectToWhatsApp(), delay)
    }
}

// API endpoint to send messages
app.post('/send', authenticateApiKey, validateSendMessage, async (req, res) => {
    const { to, message } = req.body

    if (!sock || metrics.connectionStatus !== 'connected') {
        logger.warn({ requestId: req.id }, 'Send attempted while disconnected')
        return res.status(503).json({ error: 'WhatsApp not connected' })
    }

    try {
        const formattedTo = to.includes('@') ? to : `${to}@s.whatsapp.net`

        await sock.sendMessage(formattedTo, { text: message })
        metrics.messagesSent++

        logger.info({ requestId: req.id, to: formattedTo }, 'Message sent via API')
        res.json({ success: true, message: 'Message sent', request_id: req.id })
    } catch (error) {
        metrics.errors++
        logger.error({ requestId: req.id, error: error.message }, 'Failed to send message via API')
        res.status(500).json({ error: 'Failed to send message' })
    }
})

// API endpoint to send images
app.post('/send-image', authenticateApiKey, async (req, res) => {
    const { to, image, caption } = req.body

    if (!sock || metrics.connectionStatus !== 'connected') {
        logger.warn({ requestId: req.id }, 'Send image attempted while disconnected')
        return res.status(503).json({ error: 'WhatsApp not connected' })
    }

    if (!to || !image || !image.url) {
        logger.warn({ requestId: req.id }, 'Invalid send image request')
        return res.status(400).json({ error: 'Missing required fields: to, image.url' })
    }

    try {
        const formattedTo = to.includes('@') ? to : `${to}@s.whatsapp.net`

        // Send image message
        const messagePayload = {
            image: { url: image.url }
        }

        // Add caption if provided
        if (caption) {
            messagePayload.caption = caption
        }

        await sock.sendMessage(formattedTo, messagePayload)
        metrics.messagesSent++

        logger.info({
            requestId: req.id,
            to: formattedTo,
            imageUrl: image.url
        }, 'Image sent via API')

        res.json({ success: true, message: 'Image sent', request_id: req.id })
    } catch (error) {
        metrics.errors++
        logger.error({
            requestId: req.id,
            error: error.message,
            to: to,
            imageUrl: image?.url
        }, 'Failed to send image via API')
        res.status(500).json({ error: 'Failed to send image' })
    }
})

// Health check endpoint
app.get('/health', (req, res) => {
    const uptime = Date.now() - metrics.startTime
    const isHealthy = metrics.connectionStatus === 'connected'

    const health = {
        status: isHealthy ? 'healthy' : 'unhealthy',
        connection: metrics.connectionStatus,
        uptime: Math.floor(uptime / 1000),
        timestamp: new Date().toISOString()
    }

    res.status(isHealthy ? 200 : 503).json(health)
})

// Metrics endpoint
app.get('/metrics', authenticateApiKey, (req, res) => {
    const uptime = Date.now() - metrics.startTime

    res.json({
        uptime_seconds: Math.floor(uptime / 1000),
        connection_status: metrics.connectionStatus,
        reconnect_attempts: metrics.reconnectAttempts,
        messages_received: metrics.messagesReceived,
        messages_sent: metrics.messagesSent,
        errors: metrics.errors,
        last_message_time: metrics.lastMessageTime ? new Date(metrics.lastMessageTime).toISOString() : null,
        success_rate: metrics.messagesReceived > 0
            ? ((metrics.messagesReceived - metrics.errors) / metrics.messagesReceived * 100).toFixed(2) + '%'
            : 'N/A'
    })
})

// Global error handler
app.use((err, req, res, next) => {
    metrics.errors++
    logger.error({
        requestId: req.id,
        error: err.message,
        stack: err.stack
    }, 'Unhandled error')

    if (err.message.includes('CORS')) {
        return res.status(403).json({ error: 'CORS policy violation' })
    }

    res.status(500).json({ error: 'Internal server error' })
})

// 404 handler
app.use((req, res) => {
    logger.warn({ requestId: req.id, url: req.url }, 'Route not found')
    res.status(404).json({ error: 'Not found' })
})

// Graceful shutdown
let isShuttingDown = false

async function gracefulShutdown(signal) {
    if (isShuttingDown) return
    isShuttingDown = true

    logger.info({ signal }, 'Shutting down gracefully...')

    if (server) {
        server.close(() => {
            logger.info('HTTP server closed')
        })
    }

    if (sock) {
        try {
            await sock.logout()
            logger.info('WhatsApp logged out')
        } catch (error) {
            logger.error({ error: error.message }, 'Error during logout')
        }
    }

    setTimeout(() => {
        logger.warn('Forcing shutdown after timeout')
        process.exit(1)
    }, 10000)

    logger.info('Shutdown complete')
    process.exit(0)
}

process.on('SIGINT', () => gracefulShutdown('SIGINT'))
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))

// Unhandled rejection handler
process.on('unhandledRejection', (reason, promise) => {
    metrics.errors++
    logger.error({ reason, promise }, 'Unhandled Promise Rejection')
})

// Uncaught exception handler
process.on('uncaughtException', (error) => {
    metrics.errors++
    logger.fatal({ error: error.message, stack: error.stack }, 'Uncaught Exception')
    gracefulShutdown('uncaughtException')
})

// Start server
async function start() {
    try {
        validateEnvironment()

        server = app.listen(CONFIG.PORT, () => {
            logger.info({ port: CONFIG.PORT }, 'Server started')
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            console.log('🚀 Baileys WhatsApp Server v2.0')
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
            console.log(`📡 Server: http://localhost:${CONFIG.PORT}`)
            console.log(`🔗 Backend: ${CONFIG.BACKEND_URL}`)
            console.log(`🔒 Security: Enabled`)
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

            connectToWhatsApp()
        })
    } catch (error) {
        logger.fatal({ error: error.message }, 'Failed to start server')
        process.exit(1)
    }
}

start()
