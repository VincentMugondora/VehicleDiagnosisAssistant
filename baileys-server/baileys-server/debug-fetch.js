#!/usr/bin/env node
/**
 * Debug fetch behavior to understand why Baileys fails
 */

const testUrls = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Catalytic_converter.jpg/320px-Catalytic_converter.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Catalytic_converter.jpg/256px-Catalytic_converter.jpg",
    "https://httpbin.org/image/png",
    "https://picsum.photos/400/300",
    "http://localhost:8000/static/images/test.jpg"
];

async function testFetch(url) {
    console.log(`\nTesting: ${url}`);
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });

        console.log(`  Status: ${response.status} ${response.statusText}`);
        console.log(`  OK: ${response.ok}`);
        console.log(`  Content-Type: ${response.headers.get('content-type')}`);
        console.log(`  Content-Length: ${response.headers.get('content-length')}`);

        if (!response.ok) {
            const text = await response.text();
            console.log(`  Error body: ${text.substring(0, 100)}`);
        }

    } catch (error) {
        console.error(`  [ERROR] ${error.message}`);
    }
}

async function main() {
    console.log('='.repeat(70));
    console.log('BAILEYS FETCH DEBUG TEST');
    console.log('='.repeat(70));

    for (const url of testUrls) {
        await testFetch(url);
    }

    console.log('\n' + '='.repeat(70));
}

main();
