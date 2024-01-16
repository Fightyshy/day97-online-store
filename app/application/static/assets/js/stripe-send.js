// This is a public sample test API key.
// Don’t submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.

// NOTE: Currently using own stripe api key
const stripe = Stripe("pk_test_51ONsITEk3v1yt26zhlbr7VIoOHZ8yHINbaVwXYFkUH3ArAam0RJtMQ1nrpzbVimwTxqSrRy71pChRaggJEMJ2B1S00ks6Xci6Q");

initialize();

// Create a Checkout Session as soon as the page loads
async function initialize() {
  const response = await fetch("/create-checkout-session", {
    method: "POST",
  });

  const { clientSecret } = await response.json();

  const checkout = await stripe.initEmbeddedCheckout({
    clientSecret,
  });

  // Mount Checkout
  checkout.mount('#checkout');
}