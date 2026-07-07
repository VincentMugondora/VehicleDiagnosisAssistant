#!/usr/bin/env node
/**
 * Test script to capture exact error when sending image
 */
const axios = require('axios');

const API_KEY = 'a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298';

async function testImageSend() {
    console.log('='.repeat(70));
    console.log('BAILEYS IMAGE SEND DEBUG TEST');
    console.log('='.repeat(70));

    const payload = {
        to: "263771234567",
        image: {
            url: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Catalytic_converter.jpg/320px-Catalytic_converter.jpg"
        },
        caption: "Test Catalytic Converter"
    };

    console.log('\n[1] Payload:');
    console.log(JSON.stringify(payload, null, 2));

    console.log('\n[2] Sending to: POST http://localhost:3000/send-image');

    try {
        const response = await axios.post('http://localhost:3000/send-image', payload, {
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            timeout: 30000,
            validateStatus: () => true // Accept all status codes
        });

        console.log('\n[3] Response:');
        console.log(`   Status: ${response.status}`);
        console.log(`   Data: ${JSON.stringify(response.data, null, 2)}`);

        if (response.status !== 200) {
            console.log('\n[ERROR] Image send failed!');
            console.log('   Expected: 200');
            console.log(`   Got: ${response.status}`);

            // Check server logs
            console.log('\n[4] Check server logs for detailed error');
            console.log('   Look for: "Failed to send image via API"');
            process.exit(1);
        } else {
            console.log('\n[SUCCESS] Image sent!');
            process.exit(0);
        }

    } catch (error) {
        console.error('\n[FATAL ERROR]');
        console.error(`   Message: ${error.message}`);
        console.error(`   Code: ${error.code}`);
        if (error.response) {
            console.error(`   Response Status: ${error.response.status}`);
            console.error(`   Response Data: ${JSON.stringify(error.response.data)}`);
        }
        process.exit(1);
    }
}

testImageSend();
