const $ = selector => document.querySelector(selector);

const state = {
  place: null,
  air: null,
  weather: null,
  timer: null
};


const api = {

  geo: name =>
    `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(name)}&count=6&language=en&format=json`,

  air: (lat, lon) =>
    `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone&hourly=us_aqi,pm2_5,pm10&forecast_hours=24&timezone=auto`,

  weather: (lat, lon) =>
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&hourly=temperature_2m,uv_index&forecast_hours=24&timezone=auto`

};


async function fetchData(url){

  const response = await fetch(url);

  if(!response.ok){
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();

}


function setLoading(isLoading){

  $("#loading").hidden = !isLoading;

  if(isLoading){
    $("#dashboard").hidden = true;
  }

}


function showError(message){

  $("#errorBox").textContent = message;

  $("#errorBox").hidden = false;

}


function clearError(){

  $("#errorBox").hidden = true;

}


function formatTime(dateString){

  try{

    return new Intl.DateTimeFormat([],{
      hour:"numeric",
      minute:"2-digit"
    }).format(new Date(dateString));

  }catch{

    return "now";

  }

}


function aqiInfo(aqi){

  if(aqi <= 50){

    return {
      label:"Good",
      title:"Air looks good",
      color:"#48e3a5",
      text:"Low pollution. Outdoor activity is generally comfortable for most people.",
      pct:Math.max(5,aqi / 5)
    };

  }


  if(aqi <= 100){

    return {
      label:"Moderate",
      title:"Air is acceptable",
      color:"#ffd166",
      text:"Sensitive people may notice effects. Consider lighter outdoor exposure if you feel symptoms.",
      pct:20 + (aqi - 50) / 2.5
    };

  }


  if(aqi <= 150){

    return {
      label:"Unhealthy for Sensitive Groups",
      title:"Take some care",
      color:"#ff9f43",
      text:"Sensitive groups should reduce prolonged or heavy outdoor exertion.",
      pct:40 + (aqi - 100) / 2.5
    };

  }


  if(aqi <= 200){

    return {
      label:"Unhealthy",
      title:"Reduce exposure",
      color:"#ff6f61",
      text:"Consider reducing prolonged outdoor activity and improving indoor air quality.",
      pct:60 + (aqi - 150) / 2.5
    };

  }


  if(aqi <= 300){

    return {
      label:"Very Unhealthy",
      title:"Protect yourself",
      color:"#c77dff",
      text:"Health effects are more likely. Limit outdoor exposure and follow local guidance.",
      pct:80 + (aqi - 200) / 5
    };

  }


  return {
    label:"Hazardous",
    title:"Stay protected",
    color:"#ff5c72",
    text:"Avoid prolonged outdoor exposure. Keep indoor air as clean as practical.",
    pct:100
  };

}


function weatherText(code){

  const map = {

    0:["Clear sky","☀"],
    1:["Mainly clear","🌤"],
    2:["Partly cloudy","⛅"],
    3:["Overcast","☁"],
    45:["Fog","🌫"],
    48:["Rime fog","🌫"],
    51:["Light drizzle","🌦"],
    53:["Drizzle","🌦"],
    55:["Heavy drizzle","🌧"],
    61:["Light rain","🌦"],
    63:["Rain","🌧"],
    65:["Heavy rain","🌧"],
    71:["Light snow","🌨"],
    73:["Snow","🌨"],
    75:["Heavy snow","❄"],
    80:["Rain showers","🌦"],
    81:["Rain showers","🌧"],
    82:["Heavy showers","⛈"],
    95:["Thunderstorm","⛈"],
    96:["Thunderstorm + hail","⛈"],
    99:["Thunderstorm + hail","⛈"]

  };

  return map[code] || ["Mixed conditions","☁"];

}


function pollutantLevel(name,value){

  const thresholds = {

    pm2_5:[12,35,55],
    pm10:[54,154,254],
    nitrogen_dioxide:[100,200,400],
    ozone:[100,160,240],
    carbon_monoxide:[4000,10000,30000],
    sulphur_dioxide:[40,100,200]

  };

  const t = thresholds[name] || [50,150,300];

  if(value <= t[0]) return "Low";

  if(value <= t[1]) return "Moderate";

  if(value <= t[2]) return "High";

  return "Very high";

}


function renderPollutants(){

  const items = [

    ["PM2.5","pm2_5","Fine particles","µg/m³"],
    ["PM10","pm10","Coarse particles","µg/m³"],
    ["NO₂","nitrogen_dioxide","Nitrogen dioxide","µg/m³"],
    ["O₃","ozone","Ground-level ozone","µg/m³"],
    ["CO","carbon_monoxide","Carbon monoxide","µg/m³"],
    ["SO₂","sulphur_dioxide","Sulphur dioxide","µg/m³"]

  ];


  $("#pollutants").innerHTML = items.map(
    ([label,key,description,unit]) => {

      const value = Number(
        state.air.current?.[key] ?? 0
      );

      const max =
        key === "pm2_5"
          ? 100
          : key === "pm10"
          ? 300
          : key === "carbon_monoxide"
          ? 30000
          : 500;

      const percentage =
        Math.min(
          100,
          value / max * 100
        );


      return `

        <div class="pollutant glass">

          <div class="p-top">

            <span>${label}</span>

            <span>
              ${pollutantLevel(key,value)}
            </span>

          </div>

          <strong>
            ${Number.isFinite(value) ? value.toFixed(1) : "—"}
          </strong>

          <small>
            ${description} · ${unit}
          </small>

          <div class="p-bar">
            <span style="width:${Math.max(3,percentage)}%"></span>
          </div>

        </div>

      `;

    }
  ).join("");

}


function renderAdvice(aqi){

  const severe = aqi > 150;
  const sensitive = aqi > 100;


  const advice = [

    [
      severe ? "↟" : "↗",
      "Outdoor activity",

      severe
        ? "Keep strenuous outdoor activity to a minimum and consider moving exercise indoors."
        : sensitive
        ? "Sensitive people should reduce prolonged or strenuous outdoor activity."
        : "Outdoor activity is generally reasonable; stay aware of changing conditions."
    ],

    [
      "⌂",
      "Indoor air",

      severe
        ? "Close windows during peak pollution and use filtration or clean-air strategies if available."
        : "Ventilate when outdoor air is cleaner; avoid adding indoor smoke or strong fumes."
    ],

    [
      "◉",
      "Personal protection",

      sensitive
        ? "If you must spend time outside, consider appropriate particulate protection where suitable."
        : "No special protection is usually needed at this risk level; follow local public-health advice."
    ]

  ];


  $("#adviceGrid").innerHTML = advice.map(
    ([icon,title,text]) => `

      <article class="advice glass">

        <div class="advice-icon">
          ${icon}
        </div>

        <h4>
          ${title}
        </h4>

        <p>
          ${text}
        </p>

      </article>

    `
  ).join("");

}


function renderChart(){

  const values =
    state.air.hourly?.us_aqi || [];

  const times =
    state.air.hourly?.time || [];

  const step =
    Math.max(
      1,
      Math.floor(values.length / 12)
    );

  const selected = [];


  for(
    let i = 0;
    i < values.length &&
    selected.length < 12;
    i += step
  ){

    selected.push(i);

  }


  $("#chart").innerHTML =
    selected.map(i => {

      const value =
        Number(values[i] || 0);

      const height =
        Math.max(
          4,
          Math.min(
            100,
            value / 300 * 100
          )
        );


      return `

        <div
          class="bar"
          style="height:${height}%"
        >

          <span>
            ${Math.round(value)}
          </span>

        </div>

      `;

    }).join("");


  $("#chartLabels").innerHTML =
    selected.map(
      i => `<span>${formatTime(times[i])}</span>`
    ).join("");

}


function render(){

  const aqi =
    Math.round(
      Number(
        state.air.current?.us_aqi ?? 0
      )
    );


  const info =
    aqiInfo(aqi);


  const current =
    state.weather.current || {};


  const [
    weatherDescription,
    weatherIcon
  ] =
    weatherText(
      current.weather_code
    );


  $("#locationName").textContent =
    `${state.place.name}${
      state.place.admin1
        ? ", " + state.place.admin1
        : ""
    }`;


  $("#updatedAt").textContent =
    `Updated ${
      formatTime(
        state.air.current?.time ||
        new Date().toISOString()
      )
    } · ${
      state.place.country || ""
    }`;


  $("#aqiValue").textContent =
    aqi;


  $("#aqiStatus").textContent =
    info.label;


  $("#aqiStatus").style.color =
    info.color;


  $("#aqiStatus").style.background =
    `${info.color}18`;


  $("#riskTitle").textContent =
    info.title;


  $("#riskText").textContent =
    info.text;


  $("#riskBar").style.width =
    `${info.pct}%`;


  $("#riskBar").style.background =
    info.color;


  $("#gauge").style.setProperty(
    "--gauge",
    info.color
  );


  $("#gauge").style.setProperty(
    "--gauge-angle",
    `${info.pct}%`
  );


  $("#temperature").textContent =
    Math.round(
      current.temperature_2m ?? 0
    );


  $("#humidity").textContent =
    `${Math.round(
      current.relative_humidity_2m ?? 0
    )}%`;


  $("#wind").textContent =
    `${Math.round(
      current.wind_speed_10m ?? 0
    )} km/h`;


  $("#weatherIcon").textContent =
    weatherIcon;


  $("#weatherText").textContent =
    weatherDescription;


  const uv =
    state.weather.hourly?.uv_index?.[0] ?? 0;


  $("#uv").textContent =
    Number(uv).toFixed(1);


  renderPollutants();

  renderAdvice(aqi);

  renderChart();

}


async function loadPlace(place){

  clearError();

  setLoading(true);

  $("#suggestions").innerHTML = "";


  try{

    state.place = place;


    const [
      air,
      weather
    ] = await Promise.all([

      fetchData(
        api.air(
          place.latitude,
          place.longitude
        )
      ),

      fetchData(
        api.weather(
          place.latitude,
          place.longitude
        )
      )

    ]);


    state.air = air;

    state.weather = weather;


    render();


    $("#dashboard").hidden = false;

    setLoading(false);


    localStorage.setItem(
      "airguard:lastPlace",
      JSON.stringify(place)
    );


    if(state.timer){

      clearInterval(state.timer);

    }


    state.timer =
      setInterval(
        () => loadPlace(state.place),
        15 * 60 * 1000
      );


  }catch(error){

    console.error(error);

    setLoading(false);

    showError(
      "AIR-GUARD could not load environmental data. Check your connection and try again."
    );

  }

}


async function searchLocations(query){

  if(query.trim().length < 2){

    $("#suggestions").innerHTML = "";

    return;

  }


  try{

    const data =
      await fetchData(
        api.geo(query.trim())
      );


    const results =
      data.results || [];


    $("#suggestions").innerHTML =
      results.map(
        (place,index) => `

          <button data-index="${index}">

            ${place.name}

            ${
              place.admin1
                ? ", " + place.admin1
                : ""
            }

            ·

            ${place.country || ""}

          </button>

        `
      ).join("");


    $("#suggestions")
      .querySelectorAll("button")
      .forEach(button => {

        button.onclick = () => {

          loadPlace(
            results[
              Number(
                button.dataset.index
              )
            ]
          );

        };

      });


  }catch{

    $("#suggestions").innerHTML = "";

  }

}


function locate(){

  clearError();


  if(!navigator.geolocation){

    showError(
      "Geolocation is not supported by this browser."
    );

    return;

  }


  setLoading(true);


  navigator.geolocation.getCurrentPosition(

    async position => {

      try{

        const latitude =
          position.coords.latitude;

        const longitude =
          position.coords.longitude;


        const data =
          await fetchData(
            `https://geocoding-api.open-meteo.com/v1/reverse?latitude=${latitude}&longitude=${longitude}&language=en&format=json`
          );


        const place =
          data.results?.[0] || {

            name:"My location",

            latitude,

            longitude,

            country:""

          };


        place.latitude = latitude;

        place.longitude = longitude;


        await loadPlace(place);


      }catch{

        setLoading(false);

        showError(
          "Could not identify your location. Search for your city instead."
        );

      }

    },

    () => {

      setLoading(false);

      showError(
        "Location access was denied. You can still search for any city."
      );

    },

    {
      enableHighAccuracy:true,
      timeout:10000
    }

  );

}


let searchDebounce;


$("#locationInput").addEventListener(
  "input",
  event => {

    clearTimeout(searchDebounce);


    searchDebounce =
      setTimeout(
        () =>
          searchLocations(
            event.target.value
          ),
        280
      );

  }
);


$("#locationInput").addEventListener(
  "keydown",
  event => {

    if(event.key === "Enter"){

      $("#searchBtn").click();

    }

  }
);


$("#searchBtn").onclick =
  async () => {

    const query =
      $("#locationInput")
        .value
        .trim();


    if(!query){

      showError(
        "Enter a city or location to analyze."
      );

      return;

    }


    const data =
      await fetchData(
        api.geo(query)
      ).catch(
        () => null
      );


    if(
      !data ||
      !data.results ||
      !data.results.length
    ){

      showError(
        "Location not found. Try a larger city name."
      );

      return;

    }


    loadPlace(
      data.results[0]
    );

  };


$("#locateBtn").onclick =
  locate;


$("#themeBtn").onclick =
  () => {

    document.body.classList.toggle(
      "light"
    );


    localStorage.setItem(

      "airguard:theme",

      document.body.classList.contains("light")
        ? "light"
        : "dark"

    );

  };


document.addEventListener(
  "click",
  event => {

    if(
      !event.target.closest(
        ".search-panel"
      )
    ){

      $("#suggestions").innerHTML = "";

    }

  }
);


(function init(){

  if(
    localStorage.getItem(
      "airguard:theme"
    ) === "light"
  ){

    document.body.classList.add(
      "light"
    );

  }


  const last =
    JSON.parse(
      localStorage.getItem(
        "airguard:lastPlace"
      ) || "null"
    );


  if(last){

    loadPlace(last);

  }else{

    loadPlace({

      name:"Lahore",

      country:"Pakistan",

      admin1:"Punjab",

      latitude:31.5204,

      longitude:74.3587

    });

  }

})();
