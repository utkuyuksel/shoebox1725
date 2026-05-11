# RevenueCat Product Setup Checklist

This is the step-by-step the founder runs **once Apple Developer + Google Play
Developer accounts exist**. Until then, the mobile app uses RevenueCat's test
SDK key and the paywall just shows "No subscription plans are configured yet"
in place of the offering list — that's the intended state.

The mobile client already reads:

* `AppEnv.revenueCatSdkKey` (currently `test_iKMYaaCRGMWMzdZILRgbHLSdRQX`)
* `AppEnv.premiumEntitlement` (`"premium"`)

So the dashboard work has to match those two values.

---

## 1. Create products in the stores first

**App Store Connect → My Apps → Shoebox → Subscriptions:**

Create one subscription group called `premium` with three products. Pricing
below is the suggested launch ladder; tweak in dashboard, not in code.

| Product ID                | Type             | Price tier (USD)   | Notes |
|---------------------------|------------------|--------------------|-------|
| `shoebox.premium.monthly` | Auto-renewable   | $4.99/mo (Tier 5)  | Default selected in paywall |
| `shoebox.premium.yearly`  | Auto-renewable   | $39.99/yr (Tier 40)| 33 % savings vs monthly — anchor for value |
| `shoebox.premium.lifetime`| Non-renewing     | $79.99 (Tier 80)   | One-time, no auto-renew |

All three carry a 3-day free trial (introductory offer) for the monthly only —
yearly buyers self-select for commitment and don't need the trial pull.

**Google Play Console → Monetize → Products → Subscriptions:** create the
matching three products with the **same product IDs**. RevenueCat keys
products by ID across stores.

## 2. Wire them in RevenueCat

1. Log into <https://app.revenuecat.com/projects/a9f0a9f4>.
2. **Products** → add three products with the IDs from step 1. For each,
   pick "Auto-import from store" so RC pulls metadata.
3. **Entitlements** → create one entitlement called exactly `premium`
   (lowercase, matches `AppEnv.premiumEntitlement`). Attach all three
   products to it.
4. **Offerings** → create one offering called `default` (RC convention).
   * Identifier: `default`
   * Packages:
     * `$rc_monthly` → attach `shoebox.premium.monthly`
     * `$rc_annual`  → attach `shoebox.premium.yearly`
     * Custom: `lifetime` → attach `shoebox.premium.lifetime`
5. Promote it to "current offering". The mobile app fetches this via
   `Purchases.getOfferings().current` and renders the package list.

## 3. Swap the SDK keys

When real apps are submitted, AppStore + Play assign platform-specific keys
under **RevenueCat → Project settings → API keys**:

* iOS: `appl_XXXXXXXXXXXXXXXX`
* Android: `goog_XXXXXXXXXXXXXXXX`

Set both at build time so each platform picks its own:

```bash
flutter build ios   --dart-define=REVENUECAT_SDK_KEY=appl_XXXX
flutter build apk   --dart-define=REVENUECAT_SDK_KEY=goog_XXXX
```

(The current `test_iKMYaaCRGMWMzdZILRgbHLSdRQX` works for both platforms in
sandbox but is rejected by App Store review.)

## 4. Webhook to our backend

RevenueCat → **Integrations → Webhooks** → add:

* URL: `https://api.shoebox.app/v1/revenuecat/webhook` (replace with the real
  Fly.io host once we deploy).
* Auth header: `Authorization: Bearer <REVENUECAT_WEBHOOK_SECRET>` — generate
  a random 32-char secret, paste in dashboard, also store in our Fly.io
  secrets so the backend can verify.

The backend route is not yet implemented; it will mirror entitlements into
the `users.is_premium` column so server-side endpoints can gate content
without depending on the client's claimed status.

## 5. Sandbox testing

* **iOS:** App Store Connect → Users and Access → Sandbox Testers → create
  one with a fake email. On the device, Settings → App Store → sign out of
  prod, sign in with sandbox tester. Test purchases are free and auto-renew
  in minutes (not days).
* **Android:** Internal testing track → upload a debug AAB → invite your
  google account to the closed test list → purchases use the test card
  RevenueCat generates.

After a sandbox purchase, watch the RC dashboard `Customer Lookup` tab —
the entitlement should appear in <10 seconds. If the app's premium provider
doesn't flip, pull-to-refresh the home screen (forces `customerInfoProvider`
to re-fetch) or kill the app and relaunch.

## 6. Pre-launch gotchas

* App Store **requires** a working `Restore Purchases` button on the paywall.
  We already have one — just verify it actually calls
  `Purchases.restorePurchases()` end-to-end.
* App Store **requires** linking to Terms of Service AND Privacy Policy from
  the paywall. We don't have those pages yet — add before submission.
* Yearly subscriptions can't have introductory offers in some regions
  (Turkey is one). Test the paywall in the TR locale: if "3 days free" shows
  on the yearly card, RC will reject the offer at purchase time. Better to
  drop the trial from yearly entirely.
* Apple charges 30 % first year, 15 % after — don't be surprised by the
  net revenue numbers. Same with Google. RC dashboard shows gross; check
  the App Store / Play Console reports for net.
