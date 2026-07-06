#!/usr/bin/env node
/**
 * Cache system diagram images locally in Baileys server.
 *
 * Downloads all images from Wikimedia to ./cached-images/ directory,
 * then updates the database to point to the local URLs.
 *
 * This eliminates the 18-53s delay caused by WhatsApp re-downloading
 * from Wikimedia on every request.
 *
 * Usage:
 *   node cache-images.js [--dry-run]
 */

const https = require('https')
const http = require('http')
const fs = require('fs')
const path = require('path')
const crypto = require('crypto')
const { createClient } = require('@supabase/supabase-js')

require('dotenv').config({ path: '../.env' })

const CACHE_DIR = path.join(__dirname, 'cached-images')
const BASE_URL = process.env.BAILEYS_BASE_URL || 'http://localhost:3000'

// Supabase client
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_KEY
)

/**
 * Download file from URL
 */
function downloadFile(url) {
    return new Promise((resolve, reject) => {
        const client = url.startsWith('https') ? https : http

        // Add User-Agent to avoid 403
        const options = {
            headers: {
                'User-Agent': 'VehicleDiagnosisBot/1.0 (Educational system; images cached locally)'
            }
        }

        client.get(url, options, (response) => {
            if (response.statusCode === 301 || response.statusCode === 302) {
                // Follow redirect
                return downloadFile(response.headers.location).then(resolve).catch(reject)
            }

            if (response.statusCode !== 200) {
                return reject(new Error(`HTTP ${response.statusCode}: ${url}`))
            }

            const chunks = []
            response.on('data', (chunk) => chunks.push(chunk))
            response.on('end', () => resolve(Buffer.concat(chunks)))
            response.on('error', reject)
        }).on('error', reject)
    })
}

/**
 * Get file extension from URL or default to .jpg
 */
function getExtension(url) {
    const match = url.match(/\.(jpg|jpeg|png|gif|svg|webp)(\?|$)/i)
    if (match) {
        return match[1] === 'jpeg' ? 'jpg' : match[1].toLowerCase()
    }
    return 'jpg'
}

/**
 * Sanitize system name for filename
 */
function sanitizeFilename(name) {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

/**
 * Cache all diagrams
 */
async function cacheAllDiagrams(dryRun = false) {
    console.log('============================================================')
    console.log('System Diagram Image Caching Tool (Baileys)')
    console.log('============================================================\n')

    // Create cache directory
    if (!dryRun && !fs.existsSync(CACHE_DIR)) {
        fs.mkdirSync(CACHE_DIR, { recursive: true })
        console.log(`Created cache directory: ${CACHE_DIR}\n`)
    }

    // Fetch all diagrams
    console.log('Fetching diagrams from database...')
    const { data: diagrams, error } = await supabase
        .from('system_diagrams')
        .select('id, system, image_url, source')
        .order('system')

    if (error) {
        throw new Error(`Database error: ${error.message}`)
    }

    console.log(`Found ${diagrams.length} diagrams to cache\n`)

    let cached = 0
    let skipped = 0
    let errors = 0

    for (let i = 0; i < diagrams.length; i++) {
        const diagram = diagrams[i]
        const num = i + 1

        console.log(`[${num}/${diagrams.length}] Processing: ${diagram.system}`)

        // Skip if already cached (not a wikimedia URL)
        if (!diagram.image_url.includes('wikimedia.org') && !diagram.image_url.includes('wikipedia.org')) {
            console.log('  ⏭️  Already cached (not a Wikimedia URL)\n')
            skipped++
            continue
        }

        try {
            // Download image
            console.log(`  Downloading from: ${diagram.image_url.substring(0, 80)}...`)
            const imageBuffer = await downloadFile(diagram.image_url)
            console.log(`  Downloaded ${imageBuffer.length} bytes`)

            // Generate filename
            const extension = getExtension(diagram.image_url)
            const filename = `${sanitizeFilename(diagram.system)}.${extension}`
            const filepath = path.join(CACHE_DIR, filename)
            const cachedUrl = `${BASE_URL}/cached-images/${filename}`

            console.log(`  Local path: ${filepath}`)
            console.log(`  Public URL: ${cachedUrl}`)

            if (dryRun) {
                console.log(`  [DRY RUN] Would save ${imageBuffer.length} bytes to ${filepath}`)
                console.log(`  [DRY RUN] Would update database with ${cachedUrl}`)
            } else {
                // Save to disk
                fs.writeFileSync(filepath, imageBuffer)
                console.log('  ✅ Saved to disk')

                // Update database
                const { error: updateError } = await supabase
                    .from('system_diagrams')
                    .update({
                        image_url: cachedUrl,
                        source: `${diagram.source} (cached locally)`
                    })
                    .eq('id', diagram.id)

                if (updateError) {
                    throw new Error(`Database update failed: ${updateError.message}`)
                }

                console.log('  ✅ Database updated')
                cached++
            }

            // Rate limit
            await new Promise(resolve => setTimeout(resolve, 1000))

        } catch (err) {
            console.log(`  ❌ Error: ${err.message}`)
            errors++
        }

        console.log()
    }

    // Summary
    console.log('============================================================')
    console.log('Summary:')
    console.log(`  Total diagrams: ${diagrams.length}`)
    console.log(`  ✅ Cached: ${cached}`)
    console.log(`  ⏭️  Skipped (already cached): ${skipped}`)
    console.log(`  ❌ Errors: ${errors}`)

    if (dryRun) {
        console.log('\n[DRY RUN] No changes were made. Run without --dry-run to cache images.')
    }
}

// Main
const dryRun = process.argv.includes('--dry-run')

cacheAllDiagrams(dryRun)
    .then(() => {
        console.log('\n✅ Done!')
        process.exit(0)
    })
    .catch((err) => {
        console.error(`\n❌ Fatal error: ${err.message}`)
        console.error(err.stack)
        process.exit(1)
    })
