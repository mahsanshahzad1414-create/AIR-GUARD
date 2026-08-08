// AIR-GUARD — Environmental Intelligence Engine

const app = {
  location: null,
  airQuality: null,
  weather: null,
  lastUpdated: null
};

function setLocation(city) {
  app.location = city.trim();
  console.log("Location:", app.location);
}

function showStatus(message) {
  const result = document.getElementById("result");

  if (result) {
    result.innerHTML = `<p>${message}</p>`;
  }
}

function checkLocation() {
  const input = document.getElementById("location");

  if (!input || !input.value.trim()) {
    showStatus("Please enter a city or area.");
    return;
  }

  setLocation(input.value);

  showStatus(
    `Preparing verified environmental data for ${app.location}...`
  );
}
