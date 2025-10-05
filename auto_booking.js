const { chromium } = require('playwright');

// === CONFIGURATION ===
// Replace these with your actual data and selectors
const passportNumber = 'YOUR_PASSPORT_NUMBER';
const firstName = 'YOUR_FIRST_NAME';
const lastName = 'YOUR_LAST_NAME';
const dob = 'YYYY-MM-DD';
const country = 'BD';
const city = '2059';
const targetMedicalCenterName = 'BENGAL MEDICAL CENTER'; // Use your target center name
const targetMedicalCenterId = '10696'; // Use your target center ID
const bookingUrl = 'https://wafid.com/book-appointment/';

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    async function fillAndSubmitForm() {
        await page.goto(bookingUrl);

        // Fill the booking form - update these selectors as per the real form!
        await page.fill('input[name="passport"]', passportNumber);
        await page.fill('input[name="first_name"]', firstName);
        await page.fill('input[name="last_name"]', lastName);
        await page.fill('input[name="dob"]', dob);
        await page.selectOption('#id_country', country);
        await page.selectOption('#id_city', city);

        // Select medical center (if allowed)
        await page.selectOption('#id_medical_center', targetMedicalCenterId);

        // Submit the form
        await page.click('button[type="submit"]');
        await page.waitForNavigation({ timeout: 15000 });
    }

    let matched = false;
    let attempt = 0;

    while (!matched) {
        attempt++;
        console.log(`Attempt #${attempt}...`);
        await fillAndSubmitForm();

        // Extract assigned center name (update selector as per confirmation/payment page)
        let assignedCenter = '';
        try {
            assignedCenter = await page.textContent('.assigned-center-selector'); // Change selector as necessary
        } catch {
            console.log('Could not find assigned center. Retrying...');
        }

        if (assignedCenter.trim().toLowerCase() === targetMedicalCenterName.trim().toLowerCase()) {
            // Get payment URL (usually current page)
            const paymentUrl = page.url();
            console.log(`Target center matched! Payment URL: ${paymentUrl}`);
            matched = true;
        } else {
            console.log(`Assigned center "${assignedCenter}" does not match target "${targetMedicalCenterName}". Retrying...`);
            await page.waitForTimeout(5000 + Math.random() * 5000); // Wait 5-10 seconds before retry
        }
    }

    await browser.close();
})();
