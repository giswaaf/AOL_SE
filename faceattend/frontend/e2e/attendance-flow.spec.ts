import { test, expect } from '@playwright/test';

test.describe('End-to-End Flow', () => {

  test('User Registration and Login Flow', async ({ page }) => {
    // 1. Go to register page
    await page.goto('/register');

    // 2. Select Teacher Role
    await page.getByRole('button', { name: 'I am a Teacher' }).click();

    // 3. Fill Form
    const uniqueId = Date.now();
    const email = `teacher_${uniqueId}@test.com`;

    await page.locator('input[name="name"]').fill('E2E Teacher');
    await page.locator('input[name="email"]').fill(email);
    await page.locator('input[name="collegeName"]').fill('E2E University');

    // Select Branch
    await page.locator('select[name="branch"]').selectOption('cse');

    // Teacher specific
    await page.locator('input[name="employee_id"]').fill(`EMP${uniqueId}`);
    await page.locator('input[name="phone"]').fill('1234567890');

    await page.locator('input[name="password"]').fill('password123');

    // 4. Submit
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: 'Create Account' }).click();

    // 5. Verify redirection to login
    await expect(page).toHaveURL(/\/login/);

    // 6. Verify login page loaded
    await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();

    // 7. Attempt Login (Should fail due to unverified email)
    await page.getByPlaceholder('Enter your email').fill(email);
    await page.getByPlaceholder('••••••••').fill('password123');
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Expect error message
    await expect(page.getByText(/verify your email/i)).toBeVisible();
  });

  // Note: Full attendance flow requires a verified user.
  // In a real CI environment, we would seed the DB with a verified user here.
  // For now, we document the flow.
  /*
  test('Full Attendance Flow (Requires Seeded User)', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByPlaceholder('Enter your email').fill('verified@test.com');
    await page.getByPlaceholder('••••••••').fill('password123');
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Dashboard
    await expect(page).toHaveURL('/dashboard');

    // Add Student
    await page.click('text=Add Student');
    // ... fill student details ...

    // Mark Attendance
    await page.click('text=Take Attendance');
    // ... interaction ...
  });
  */
});
